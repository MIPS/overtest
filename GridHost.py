#  Copyright (C) 2012-2020 MIPS Tech LLC
#  Written by Matthew Fortune <matthew.fortune@imgtec.com> and
#  Daniel Sanders <daniel.sanders@imgtec.com>
#  This file is part of Overtest.
#
#  Overtest is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3, or (at your option)
#  any later version.
#
#  Overtest is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with overtest; see the file COPYING.  If not, write to the Free
#  Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
#  02110-1301, USA.
from utils import Utilities
import socket
import os
import Scheduler
import sys
import time
import TestManager
import signal
from Config import CONFIG
import getopt
from utils.Daemon import *
from OvertestExceptions import *
from LogManager import LogManager

# Global access to child pids
taskList = {}

class GridHost:
  """
  A host is a machine that can host tests. Hosts have attributes in the group:
  'Overtest Host'

  This class initialises a host and manages the process count.
  """
  def __init__(self, ovtDB):
    self.shuttingDown = False
    self.ovtDB = ovtDB
    self.fallbacklognumber = 0
    self.hostid = -1

  def termHandler(self, signum, frame):
    """
    Handle a sigterm gracefully
    """
    for pid in pidlist:
      try:
        os.kill(pid, signal.SIGTERM)
      except Exception, e:
        self.log.write(e)

    self.shuttingDown = True

  def run(self, args):
    """
    Create the correct number of subprocesses and reconnect each of them to the
    database.

    Also handle any remaining exceptions and log them as status
    """
    self.concurrency = 1
    self.activethreads = 0
    self.testrunid = 0

    try:
      opts, args = getopt.getopt(args, "i:j:", ["testrunid=","jobs="])
    except getopt.GetoptError, e:
      raise StartupException, "Error parsing options: %s" % str(e)

    for (o,a) in opts:
      if o in ("-j", "--jobs"):
	try:
	  self.concurrency = int(a)
	except ValueError:
	  print "jobs must be a number"
	  sys.exit(1)
	if self.concurrency < 0:
	  print "jobs must be greater than 0"
	  sys.exit(1)
      elif o in ("-i", "--testrunid"):
	try:
	  self.testrunid = int(a)
	except ValueError:
	  print "Testunid must be a number"
	  sys.exit(1)

    if self.testrunid == 0:
      print "Error: Please specify a testrunid"
      sys.exit(1)

    self.log = LogManager("grid", display=True, local=True, subdir=self.testrunid)
    self.ovtDB.registerLog(self.log)

    signal.signal(signal.SIGTERM, self.termHandler)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    signal.signal(signal.SIGUSR1, signal.SIG_IGN)
    # This allows USR2 to be used to check if the process exists using kill -USR2 <me>
    signal.signal(signal.SIGUSR2, signal.SIG_IGN)

    # Driver code
    CRASH = False
    self.ovtDB.reconnect(quiet=True)

    # Find all testruns (in order) that need tasks executing
    self.testrun = TestManager.Testrun(self.ovtDB,testrunid=self.testrunid)

    details = self.testrun.getDetails()
    if len(details) == 0:
      print "Testrun not found"
      sys.exit(1)

    if not details['status'] in ["HOSTALLOCATED", "GRIDARCHIVE", "GRIDDELETE"]:
      print "Testrun must be ready to run and not previously started"
      sys.exit(1)

    if not details['usegridengine']:
      print "Testrun is not marked as using a grid engine"
      sys.exit(1)

    hosts = self.ovtDB.getTestrunHosts(self.testrunid)
    if len(hosts) != 1:
      print "This testrun must only be assigned to one host"
      sys.exit(1)

    # Check that this testrun is intended for the HH UGE grid
    hostResource = self.ovtDB.getResources(None, hosts[0])
    hostTypes = hostResource[0][hosts[0]]['related']
    hostAttributes = hostTypes[0][hostTypes[1][0]]['related']
    foundHHUGE = False
    for attributeid in hostAttributes[1]:
      if hostAttributes[0][attributeid]['data'] == "Shared Filesystem":
	hostValues = hostAttributes[0][attributeid]['related']
	for resourceattributeid in hostValues[1]:
	  if hostValues[0][resourceattributeid]['data'] == "HH UGE":
	    foundHHUGE = True

    if not foundHHUGE:
      print "Testrun is not allocated to HH UGE"
      sys.exit(1)

    self.hostid = hosts[0]
    self.ovtDB.setHostPID(self.hostid, os.getpid())

    # Start as many tasks as possible
    self.checkConcurrency()

    while len(taskList) != 0:
      try:
        interrupted = True
        while interrupted:
          try:
            interrupted = False
            (pid, status) = os.waitpid(0, 0)
          except OSError, e:
            if e.errno == 10 or e.errno == 4:
              interrupted = True

        signo = status & 0xFF
        retval = status >> 8
	if signo != 0 or retval != 0:
          self.log.write("%s: Process with PID %u exited with signal %u and returned %u"%(time.asctime(), pid, signo, retval))

        if signo != 0 or retval != 0:
          # Exit code 1 ==> Process exited with keyboard interrupt
          # Exit code 2 ==> Process exited due to sigterm, allow a new one to start unless
          #                 this driver has been sent SIGTERM
          if not retval in [0,1,2]:
            self.log.write("%s: Process with PID %u may have crashed" % (time.asctime(), pid))

          if retval != 2 or self.shuttingDown:
            CRASH = True

	deadTask = None
	for task in taskList:
	  if taskList[task]['pid'] == pid:
	    deadTask = task
	    self.activethreads -= taskList[task]['concurrency']
	del taskList[deadTask]

	if not CRASH and signo == 0 and retval == 0:
	  self.checkConcurrency()
      except KeyboardInterrupt, e:
        sys.exit(1)

    if CRASH:
      sys.exit(1)
    else:
      sys.exit(0)

  def checkAborted(self):
    """
    returns a list of testruns ready to abort.
    Grab the testrun lock and abort them all
    """
    testruns = self.ovtDB.checkAbortedTestruns(self.testrunid)

    for testrunid in testruns:
      success = False
      while not success:
        try:
          self.ovtDB.setAutoCommit(False)
          self.ovtDB.setTestrunRunstatus(testrunid, "ABORTED")
          self.ovtDB.FORCECOMMIT()
          success = True
          self.ovtDB.setAutoCommit(True)
          self.ovtDB.cancelAllResourceRequests(testrunid)
        except DatabaseRetryException, e:
          self.ovtDB.reconnect()

  def checkConcurrency(self):
    newTasks = []
    hadNewTasks = False
    moreTasks = True
    while moreTasks and self.activethreads < self.concurrency:
      # Find a new task and mark it as started
      # This is an atomic operation that uses the testrun table as a LOCK
      task = self.testrun.getNextTask(self.hostid)
      if task == None:
	moreTasks = False
      else:
        newTasks.append(task)
      # Do not create more tasks than we can run in parallel
      if len(newTasks) == self.concurrency - self.activethreads:
        moreTasks = False

    newTaskCount = len(newTasks)
    for task in newTasks:
      hadNewTasks = True
      taskConcurrency = (self.concurrency - self.activethreads) / newTaskCount
      taskList[task] = {"concurrency" : taskConcurrency,
			"runner" : self.startTask,
		        "running" : False}
      newTaskCount -= 1
      self.activethreads += taskConcurrency

    # See if there is a pending abort
    self.checkAborted()

    # Check for archiving or deleting
    (moreTasks, delete) = self.testrun.setArchiveOrDeleteInProgress()
    newTasks = []

    while moreTasks and self.activethreads < self.concurrency:
      # Find a task to archive and mark it as started
      # This is an atomic operation that uses the testrun table as a LOCK
      task = self.testrun.getNextTaskToArchive(self.hostid)
      if task == None:
	moreTasks = False
      else:
        newTasks.append(task)
      # Do not create more tasks than we can run in parallel
      if len(newTasks) == self.concurrency - self.activethreads:
        moreTasks = False

    for task in newTasks:
      hadNewTasks = True
      taskList[task] = {"concurrency" : 1,
			"runner" : self.startDeleteTask if delete else self.startArchiveTask,
		        "running" : False}
      self.activethreads += 1

    # When the archive is complete the testrun can be marked as archived
    self.testrun.archiveComplete()

    if hadNewTasks:
      self.forkTasks()
      # reconnect... again since the existing connection will have been terminated
      # by the worker threads
      self.ovtDB.reconnect(quiet=True)
 
  def forkTasks(self):
    """
    Start processes assigning them numbers from processNumbers
    """
    for task in taskList:
      if 'pid' in taskList[task]:
	continue
      self.fallbacklognumber += 1
      pid = os.fork()
      if pid != 0:
        # I am the parent
        taskList[task]['pid'] = pid
      else:
        # Start the process
        self.taskRun(taskList[task]['runner'], task, self.fallbacklognumber)
        print "Should not see this"
        sys.exit(0)
        # DO NOT RETURN FOR THE CHILD PROCESS
        break

  def taskRun(self, taskRunner, task, lognumber):
    """
    The code to run a new worker process
    """
    # Process code
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGHUP, signal.SIG_DFL)
    self.log = LogManager("grid.%u"%(lognumber), display=True, local=True, subdir=self.testrunid)
    self.ovtDB.reconnect(quiet=True, log=self.log)
 
    innerexception = None
    try:
      try:
        taskRunner(task)
      except Exception, e:
        innerexception = formatExceptionInfo()
        try:
          self.ovtDB.FORCEROLLBACK()
        except DatabaseRetryException, e:
          self.ovtDB.reconnect()
        self.ovtDB.setAutoCommit(True)
        self.log.write("%s: %s" % (time.asctime(),innerexception))
        sys.exit(3)
    except Exception, e:
      if innerexception != None:
        self.log.write("Exception while processing inner exception.")
        self.log.write("Inner exception was:")
        self.log.write(innerexception)
      self.log.write(formatExceptionInfo())
      sys.exit(4)

  def startTask(self, task):
    """
    Find one task and start it
    """
    testrun = self.testrun
    self.exitcode = 0
    task.concurrency = taskList[task]['concurrency']
    try:
      try:
        # Run the task specific actions the runChecked wrapper
        # handles standard overtest exceptions
        try:
          # Wrap the following in a try except block to handle result submission errors
          # This is to deal with internal consistency. It 'should' only fail if multiple
          # versions of the same action exist in a testrun!
          try:
            if task.runChecked():
              testrun.submit(task.actionid, True)
          except TaskRunErrorException, e:
            # Assert failure
            testrun.submit(e.actionid, False)
            # Abort the whole testrun. Any task failure is a full failure
            testrun.setAborting(lock = True)
            testrun.logHelper("Task failed... Testrun aborted")
          except ResultSubmissionException, e:
            testrun.submit(task.actionid, False, {"__OVT_EXCEPT__":"Failed to submit result: %s"%formatExceptionInfo()})
            testrun.logHelper("Task failed to submit result")
          except TestrunAbortedException, e:
            testrun.submit(task.actionid, False, {"Aborted":"User abort or another task failed"})
            testrun.logHelper("Task aborted due to testrun abort")
          except KeyboardInterrupt, e:
            testrun.submit(task.actionid, False, {"__OVT_EXCEPT__":"Keyboard interrupt"})
            testrun.setAborting(lock = True)
            testrun.logHelper("Run interrupted, aborting")
            self.quit = True
            raise
          except Exception, e:
            testrun.submit(task.actionid, False, {"__OVT_EXCEPT__":formatExceptionInfo()})
            testrun.setAborting(lock = True)
            testrun.logHelper("Exception raised, module run code unsafe: A%u.py"%task.actionid)
        except ResultSubmissionException, e:
          # The task will not get a result which is bad but nothing can be done. It will
          # be marked as complete below so should not be run in an endless loop
          # This is a catastrophic testrun failure and suggests inconsistency in the overtest internals
          testrun.setAborting(lock = True)
          testrun.logHelper("Failed to submit result for action: %u"%(task.actionid))
      finally:
        # Mark the task as complete
        testrun.setTaskEnded(task.testrunactionid)
        del task
    except KeyboardInterrupt, e:
      self.log.write("%s: %s"%(time.asctime(),"Scheduler Interrupted. Exiting"))
      self.exitcode = 1
    sys.exit(self.exitcode)

  def startDeleteTask(self, task):
    self.startArchiveTask(task, True)

  def startArchiveTask(self, task, delete = False):
    """
    Find one task and archive it
    """
    testrun = self.testrun
    self.exitcode = 0
    task.concurrency = taskList[task]['concurrency']
    try:
      try:
        try:
          # The task will delete its work directory and perform any custom cleanup
          # When deleting it will also delete its results area
          task.archiveChecked(delete)
        except Exception, e:
          testrun.logHelper("Exception raised, archive code unsafe: A%u.py"%task.actionid)
          self.log.write("Exception raised, archive code unsafe: A%u.py\n%s"%(task.actionid, formatExceptionInfo()))
      finally:
        testrun.setTaskArchived(task.testrunactionid)
        del task
    except KeyboardInterrupt, e:
      self.log.write("%s: %s"%(time.asctime(),"Scheduler Interrupted. Exiting"))
      self.exitcode = 1
    sys.exit(self.exitcode)
