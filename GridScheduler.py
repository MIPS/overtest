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
import time
import signal
from OvertestExceptions import *

class Scheduler:
  """
  The scheduler is responsible for the logic in choosing which 
  test to run from what testrun. It also drives the running of tests.
  """
  def __init__(self, host, testrunid):
    self.threadnumber = 0
    self.testrunid = testrunid
    self.host = host 
    self.quit = False
    self.exitcode = 0
    signal.signal(signal.SIGTERM, self.termHandler)
    signal.signal(signal.SIGHUP, self.termHandler)

  def logHelper(self, message):
    self.host.logHelper(self.threadnumber, message)

  def logDB(self, message):
    self.host.logDB(self.threadnumber, message)

  def termHandler(self, signum, frame):
    """
    Handle a sigterm gracefully
    """
    self.quit = True
    self.exitcode = 2
    self.logHelper("SIGTERM: Finishing current test and exiting")

  def run(self):
    """
    Continuously find and select tests to run.
    This function must be highly resilient to concurrency issues.
    """
    try:
      nothingToDo = False
      archiverHadWork = False
      self.quit = False
      while not self.quit:
        if self.host.shouldThreadExit(self.threadnumber):
          self.logHelper("Thread %u exiting by database request"%self.threadnumber)
          self.logDB("Thread %u exiting by database request"%self.threadnumber)
          self.quit = True
          break

        # Check for 'aborting' testruns, and mark them aborted as appropriate
        self.host.checkAbortedTestruns(self.testrunid)

        # Find all testruns (in order) that need tasks executing
        testruns = self.host.getNextTestruns(self.logDB)
        if not archiverHadWork and (nothingToDo or len(testruns) == 0):
          time.sleep(5)
        nothingToDo = True
        for testrun in testruns:
          # Find a new task and mark it as started
          # This is an atomic operation that uses the testrun table as a LOCK
          task = testrun.getNextTask(self.host.getHostID())
          if task == None:
            continue
          try:
            nothingToDo = False
            # Run the task specific actions the runChecked wrapper
            # handles standard overtest exceptions
            try:
              # Wrap the following in a try except block to handle result submission errors
              # This is to deal with internal consistency. It 'should' only fail if multiple
              # versions of the same action exist in a testrun!
              try:
                testrun.logHelper("TRA: %u Starting" % task.testrunactionid)
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
                self.logDB("Interrupt received, shutting down")
                self.quit = True
                raise
              except Exception, e:
                testrun.submit(task.actionid, False, {"__OVT_EXCEPT__":formatExceptionInfo()})
                testrun.setAborting(lock = True)
                testrun.logHelper("Exception raised, module run code unsafe: A%u.py"%task.actionid)
                self.logDB("Exception raised, module run code unsafe: A%u.py\n%s"%(task.actionid, formatExceptionInfo()))
            except ResultSubmissionException, e:
              # The task will not get a result which is bad but nothing can be done. It will
              # be marked as complete below so should not be run in an endless loop
              # This is a catastrophic testrun failure and suggests inconsistency in the overtest internals
              testrun.setAborting(lock = True)
              testrun.logHelper("Failed to submit result for action: %u"%(task.actionid))
              testrun.logDB("Failed to submit result for action: %u\n%s"%(task.actionid, formatExceptionInfo()))
          finally:
            # Mark the task as complete
            testrun.setTaskEnded(task.testrunactionid)
            testrun.logHelper("TRA: %u Finished" % task.testrunactionid)
            del task
          # Start from the first testrun again. This permits priority ordering
          break
    except KeyboardInterrupt, e:
      self.logHelper("Scheduler Interrupted. Exiting")
      sys.exit(1)
    sys.exit(self.exitcode)
