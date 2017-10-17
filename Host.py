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
pidlist = {}

class Host:
  """
  A host is a machine that can host tests. Hosts have attributes in the group:
  'Overtest Host'

  This class initialises a host and manages the process count.
  """
  def __init__(self, ovtDB):
    self.shuttingDown = False
    self.ovtDB = ovtDB
    self.log = LogManager(CONFIG.hostname, False)
    self.ovtDB.registerLog(self.log)
    self.pidfile = None

  def getHostID(self):
    """
    Return the host identified (a resource id)
    """
    return self.hostid

  def processRun(self, processNumber):
    """
    The code to run a new worker process
    """
    # Process code
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGHUP, signal.SIG_DFL)
    self.log = LogManager("%s.%u"%(CONFIG.hostname, processNumber), False)
    self.ovtDB.reconnect(quiet=True, log=self.log)
 
    innerexception = None
    try:
      try:
        scheduler = Scheduler.Scheduler(self, processNumber)
        scheduler.run()
      except Exception, e:
        innerexception = formatExceptionInfo()
        try:
          self.ovtDB.FORCEROLLBACK()
        except DatabaseRetryException, e:
          self.ovtDB.reconnect()
        self.ovtDB.setAutoCommit(True)
        self.logDB(processNumber, innerexception)
        self.log.write("%s: %s" % (time.asctime(),innerexception))
        sys.exit(3)
    except Exception, e:
      if innerexception != None:
        self.log.write("Exception while processing inner exception.")
        self.log.write("Inner exception was:")
        self.log.write(innerexception)
      self.log.write(formatExceptionInfo())
      sys.exit(4)

  def startProcesses(self, processNumbers, pidlist):
    """
    Start processes assigning them numbers from processNumbers
    """
    for i in processNumbers:
      pid = os.fork()
      if pid != 0:
        # I am the parent
        pidlist[pid] = i
      else:
        # Start the process
        self.processRun(i)
        print "Should not see this"
        sys.exit(0)
        # DO NOT RETURN FOR THE CHILD PROCESS
        break

  def checkConcurrency(self, pidlist):
    """
    Check the correct number of processes exist and start them
    """
    details = self.ovtDB.getHostInfo(self.name)
    if details['concurrency'] > len(pidlist):
      processNumbers = range(0, details['concurrency'])
      for PID in pidlist:
        processNumbers.remove(pidlist[PID])

      self.startProcesses(processNumbers, pidlist)
      self.ovtDB.reconnect(quiet=True)

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

  def run(self, name, args):
    """
    Create the correct number of subprocesses and reconnect each of them to the
    database.

    Also handle any remaining exceptions and log them as status
    """
    details = self.ovtDB.getHostInfo(name)
    self.name = name
    if details == None:
      raise Exception, "Failed to find host: "+name
    self.hostid = details['hostid']
    self.hostname = details['hostname']
    self.concurrency = details['concurrency']
    if socket.gethostname() != self.hostname:
      raise StartupException, "Host's hostname does not match this host: "+self.hostname + " != " +socket.gethostname()

    if details['pid'] != None and \
       Utilities.pid_exists(details['pid']) and \
       details['pid'] != os.getpid():
      raise StartupException, "Overtest daemon already running on this host: "+str(details['pid'])

    status = self.ovtDB.getResourceStatus(self.hostid)
    if status == "DISABLE" or status == "DISABLED":
      self.ovtDB.setResourceStatus(self.hostid, "DISABLED")
      raise StartupException, "Host is disabled"


    try:
      opts, args = getopt.getopt(args, "dp:", ["daemon","pidfile="])
    except getopt.GetoptError, e:
      raise StartupException, "Error parsing options: %s" % str(e)

    self.daemon = False
    self.pidfile = None
    for (o,a) in opts:
      if o in ("-d", "--daemon"):
        self.daemon = True
      elif o in ("-p", "--pidfile"):
        self.pidfile = a

    self.ovtDB.setResourceStatus(self.hostid, "OK")
    self.logDB(0, "Host started");

    signal.signal(signal.SIGTERM, self.termHandler)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    signal.signal(signal.SIGUSR1, signal.SIG_IGN)
    # This allows USR2 to be used to check if the process exists using kill -USR2 <me>
    signal.signal(signal.SIGUSR2, signal.SIG_IGN)

    try:
      if self.daemon:
        createDaemon()
    except Exception, e:
      raise StartupException, "Failed to daemonize: %s" % str(e)
  
    # Driver code
    CRASH = False
    self.ovtDB.reconnect(quiet=True)

    # Register the PID
    self.ovtDB.setHostPID(self.hostid, os.getpid())
    if self.pidfile != None:
      fh = open(a, "w")
      fh.write(str(os.getpid()))
      fh.close()

    # Perform cleanup from previous shutdown or crash
    # Fetch all tasks running on this host (there is a dead+unheld request on this host)
    # Fail all the tasks and report host crash as reason
    # Mark all resource requests as dead
    deadtasks = self.ovtDB.getRunningTasks (self.hostid)
    for taskinfo in deadtasks:
      (testrunid, testrunactionid, actionid, archived) = taskinfo

      if archived == False:
        self.ovtDB.resetArchived (testrunactionid)

      # Use the testrun class to alter the testrun
      testrun = TestManager.Testrun (self.ovtDB, testrunid=testrunid, logDB=lambda x: self.logDB(0, x))
      success = False
      while not success:
        try:
          self.ovtDB.setAutoCommit(False)

          # Mark the testrunaction as failed because of a host failure
          testrun.submit (actionid, False, {"__OVT_EXCEPT__":"Testrun failed due to Host Daemon crash"})
          testrun.setTaskEnded (testrunactionid)
          testrun.logHelper ("TRA: %u died due to host crash" % testrunactionid)

          # Trigger an abort if not already in progress
          testrun.setAborting (lock = True)

          self.ovtDB.FORCECOMMIT()
          success = True
          self.ovtDB.setAutoCommit(True)
        except DatabaseRetryException, e:
          pass

    processNumbers = range(0,self.concurrency)
    self.startProcesses(processNumbers, pidlist)
    # reconnect... again since the existing connection will have been terminated
    # by the worker threads
    self.ovtDB.reconnect(quiet=True)
 
    hoststatus = self.ovtDB.getResourceStatus(self.hostid)
    while len(pidlist) != 0 or self.concurrency == 0:
      try:
        interrupted = True
        while interrupted:
          try:
            interrupted = False
            hoststatus = self.ovtDB.getResourceStatus(self.hostid)
            if self.concurrency == 0 and hoststatus != "OK":
              break
            (pid, status) = os.waitpid(0, os.WNOHANG)
            if pid == 0:
              time.sleep(1)
              # When a thread crashes do not start new threads
              if hoststatus == "OK" and not CRASH:
                self.checkConcurrency(pidlist)
              interrupted = True
          except OSError, e:
            if e.errno == 10:
              time.sleep(1)
              # When a thread crashes do not start new threads
              if hoststatus == "OK" and not CRASH:
                self.checkConcurrency(pidlist)
              interrupted = True

            if e.errno == 4:
              interrupted = True
        if self.concurrency == 0 and hoststatus != "OK":
          break
        signo = status & 0xFF
        retval = status >> 8
	if signo != 0 or retval != 0:
          self.log.write("%s: Process %u with PID %u exited with signal %u and returned %u"%(time.asctime(),pidlist[pid], pid, signo, retval))

        details = self.ovtDB.getHostInfo(self.name)
        hoststatus = self.ovtDB.getResourceStatus(self.hostid)
        self.concurrency = details['concurrency']
        if signo != 0 or retval != 0:
          # Exit code 1 ==> Process exited with keyboard interrupt
          # Exit code 2 ==> Process exited due to sigterm, allow a new one to start unless
          #                 this driver has been sent SIGTERM
          if not retval in [0,1,2]:
            self.log.write("%s: Process %u with PID %u may have crashed" % (time.asctime(),pidlist[pid], pid))

          if retval != 2 or self.shuttingDown:
            CRASH = True
        del pidlist[pid]
      except KeyboardInterrupt, e:
        if self.concurrency == 0:
          break
        else:
          continue

    try:
      if self.pidfile != None:
        os.remove (self.pidfile)
    except OSError:
      pass

    status = self.ovtDB.getResourceStatus(self.hostid)
    if status == "OK":
      self.logDB(0, "Shutdown Host");
      self.ovtDB.setResourceStatus(self.hostid, "OFFLINE")
      sys.exit(0)
    elif status == "RESTART":
      self.logDB(0, "Restarting Host");
      self.ovtDB.setResourceStatus(self.hostid, "UPDATING")
      # Close the database connection
      del self.ovtDB
      import commands
      os.chdir(os.path.dirname(sys.argv[0]))
      update_result = commands.getstatusoutput('P4CONFIG=.p4conf ' + CONFIG.p4 + " sync")
      self.log.write(update_result[1])
      # Close the log manager
      del self.log

      # Close all file handles
      MAXFD = 1024
      sys.path.pop(0)
      import resource
      maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
      if maxfd == resource.RLIM_INFINITY:
        maxfd = MAXFD

      for fd in range (3, maxfd):
        try:
          os.close(fd)
        except OSError:
          pass
      
      if update_result[0] == 0:
        sys.argv.insert(0, CONFIG.python)
        os.execv(CONFIG.python, sys.argv)
      else:
        sys.exit(3)
    elif status == "DISABLE":
      self.logDB(0, "Disabling Host");
      self.ovtDB.setResourceStatus(self.hostid, "DISABLED")
      sys.exit(4)
    else:
      self.logDB(0, "Exiting for unknown status: %s"%status)
      sys.exit(5)

  def logDB(self, threadnumber, message):
    """
    Set the status for a given thread
    """
    self.ovtDB.appendToResourceLog(self.hostid, message, index=threadnumber)

  def logHelper(self, threadnumber, message):
    """
    Log a message for a thread
    """
    self.log.write("%s: T%u: %s"%(time.asctime(),threadnumber,message))

  def shouldThreadExit(self, threadnumber):
    """
    Decide if the specified thread should exit
    """
    details = self.ovtDB.getHostInfo(self.name)
    return threadnumber >= details['concurrency'] or self.ovtDB.getResourceStatus(self.hostid) != "OK"

  def checkAbortedTestruns(self):
    """
    returns a list of testruns ready to abort.
    Grab the testrun lock and abort them all
    """
    testruns = self.ovtDB.checkAbortedTestruns()

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

  def getNextTestruns(self, logDB):
    """
    Returns the set of testruns that this thread should try to execute next
    """
    ret = []
    for testrunid in self.ovtDB.getNextTestruns(self.hostid):
      ret.append(TestManager.Testrun(self.ovtDB,testrunid=testrunid, logDB=logDB))
    return ret

  def getTestrunsToArchiveOrDelete(self, logDB):
    """
    Returns the set of testruns that need to be archived (deletion implies archiving)
    """
    ret = []
    for testrunid in self.ovtDB.getTestrunsToArchiveOrDelete(self.hostid):
      ret.append(TestManager.Testrun(self.ovtDB,testrunid=testrunid,logDB=logDB))
    return ret

