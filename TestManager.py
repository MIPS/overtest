from Dependencies import Dependencies
from OvertestExceptions import DatabaseRetryException, ResourceException
from OvertestExceptions import formatExceptionInfo, ResourceInitFailedException
from OvertestExceptions import AllocationException, AllocationAbortException
from OvertestExceptions import ResultSubmissionException, ConfigException
from Config import CONFIG

import os
import sys
import types

class TestrunFactory:
  def __init__(self, user, ovtDB):
    self.ovtDB = ovtDB
    self.dependencies = Dependencies(self.ovtDB)
    self.userid = self.ovtDB.getUserByName(user)

  def fetchTestrun(self, testrunid):
    if not self.ovtDB.checkTestrun(testrunid, self.userid):
      return (False, "Testrun not found or owned by another user")
    versionedactioniddict = self.ovtDB.getVersionedActionidDict(testrunid)
    if self.dependencies.resolveDependencies(versionedactioniddict,
                                             autoadd=False) == None:
      return (False, "Failed to resolve dependencies. Inconsistent testrun")
    return (True, Testrun(self.ovtDB, testrunid=testrunid,
                          dependencies=self.dependencies,
                          versionedactioniddict=versionedactioniddict))

class Testrun:
  debug_allow_skipping = 0 # NOTE: Do not modify, this class doesn't support it

  def __init__(self, ovtDB, userid = None, testrunid = None,
               dependencies = None, versionedactioniddict = None, logDB = None):
    self.ovtDB = ovtDB
    self.logginglist = []
    self.logginglist.append(self.ovtDB.log.write)
    if logDB != None:
      self.logginglist.append(logDB)
    self.dependencies = dependencies
    self.versionedactioniddict = versionedactioniddict
    if testrunid == None:
      self.testrunid = self.ovtDB.createTestrun(userid, versionedactioniddict)
    else:
      self.testrunid = testrunid

    self.resources = {}

  def getTestrunid(self):
    return self.testrunid

  def logHelper(self, message):
    for log in self.logginglist:
      log("TR%u: %s" % (self.testrunid, message))

  def getDetails(self):
    """
    Fetch the relevant testrun details
    """
    return self.ovtDB.getTestrunDetails(self.testrunid)

  def getUser(self):
    """
    Fetch the user that owns this testrun
    """
    return self.ovtDB.getTestrunUser(self.testrunid)

  def getConfig(self, versionedactionid):
    if versionedactionid == None:
      return None
    return TestConfig(self, versionedactionid)

  def printTests(self, showids=False):
    if self.dependencies != None and self.versionedactioniddict != None:
      self.dependencies.printTestset(self.versionedactioniddict, ids=showids)

  def registerPID(self, versionedactionid, pid):
    """
    Register the PID for a test
    """
    self.ovtDB.registerPID(self.testrunid, versionedactionid, pid)

  def getHostPID(self):
    """
    Fetch the hostid from the database for the speicfied host
    """
    return self.ovtDB.hostpid

  def setStarted(self):
    """
    Check if the testrun is already marked as started and mark it started if not
    """
    self.ovtDB.setTestrunRunstatus(self.testrunid, "RUNNING")

  def setAborting(self, lock = False):
    """
    Assert that the testrun has failed. This will trigger an abort of everything
    """
    self.__setState ("ABORTING", lock)

  def setPaused(self, lock = False):
    """
    Pause the tesrun if possible
    """
    self.__setState ("PAUSED", lock)

  def __setState(self, state, lock = False):
    """
    Update a testrun's status
    """
    if lock:
      success = False
      while not success:
        try:
          self.ovtDB.setAutoCommit(False)
          self.ovtDB.setTestrunRunstatus(self.testrunid, state)
          self.ovtDB.FORCECOMMIT()
          success = True
          self.ovtDB.setAutoCommit(True)
        except DatabaseRetryException:
          pass
    else:
      self.ovtDB.setTestrunRunstatus(self.testrunid, state)

  def setArchiveOrDeleteInProgress(self):
    """
    Mark the testrun as archiving or deleting as appropriate
    """
    status = self.ovtDB.getTestrunRunstatus(self.testrunid)
    if status == "GRIDARCHIVE" or status == "READYTOARCHIVE" or status == "ARCHIVING":
      self.ovtDB.setTestrunRunstatus(self.testrunid, "ARCHIVING")
      return (True, False)
    if status == "GRIDDELETE" or status == "READYTODELETE" or status == "DELETING":
      self.ovtDB.setTestrunRunstatus(self.testrunid, "DELETING")
      return (True, True)
    return (False, False)

  def isAborted(self):
    """
    Return true if the testrun has been aborted
    """
    self.ovtDB.always_reconnect = False
    try:
      try:
        status = self.ovtDB.getTestrunRunstatus(self.testrunid)
        return (status == "ABORTED" or status == "ABORTING")
      except DatabaseRetryException:
        # Do not reconnect just assume no abort has occurred
        return False
    finally:
      self.ovtDB.always_reconnect = True

  def initResources(self, versionedactionid, testrunactionid, init = True):
    """
    Initialise all the resources for the given versionedactionid
    """
    resourcedata = self.ovtDB.getTestrunResources(self.testrunid,
                                                  versionedactionid)

    if len(resourcedata) == 0:
      raise ResourceInitFailedException("Failed to find Execution Host (or any other resource)")

    if not versionedactionid in self.resources:
      self.resources[versionedactionid] = {}

    for data in resourcedata:
      resource = None
      try:
        exec("from resources.R%u import *" % (data['typeid']))
        exec("resource = R%u((self, {'versionedactionid':versionedactionid}, data))"
             % (data['typeid']))
        exec("del(sys.modules['resources.R%u'])" % (data['typeid']))
      except ImportError, ex:
        raise ResourceInitFailedException("Failed to import module for %s resource (R%u) %s"
                                          % (data['name'], data['typeid'],str(ex)))
      except SyntaxError:
        raise ResourceInitFailedException("Syntax error in %s resource module (R%u)\n%s"
                                          % (data['name'], data['typeid'],
                                             formatExceptionInfo()))
      except Exception:
        raise ResourceInitFailedException("Unknown exception in %s resource module (R%u)\n%s"
                                          % (data['name'], data['typeid'],
                                             formatExceptionInfo()))

      self.resources[versionedactionid][resource.getType()] = resource

    if init:
      for restype in sorted(self.resources[versionedactionid].keys()):
        resource = self.resources[versionedactionid][restype]
        # Do the resource initialisation
        try:
          if resource.initialiseChecked():
            # Clone the resource to create historic entries. These historic
            # entries are used when searching testruns instead of the real
            # resources. This is because the real resource may change its
            # attributes over time and also the users resource requirements
            # may not fully specify a resource.
            self.ovtDB.cloneResource(resource.getResourceid(),
                                     resource.getAttributes(),
                                     testrunactionid=testrunactionid)
        except ResourceInitFailedException:
          raise
        except Exception:
          raise ResourceInitFailedException("Unknown exception during init of %s resource\n%s"
                                            % (resource.name,
                                               formatExceptionInfo()))

  def getResource(self, versionedactionid, name):
    """
    Grab a pre-initialised resource
    """
    if versionedactionid not in self.resources or \
       name not in self.resources[versionedactionid]:
      raise ResourceException("Resource %s does not exist for versioned action %d"
                              % (name, versionedactionid))

    return self.resources[versionedactionid][name]

  def getNextTask(self, hostid):
    """
    Finds the next available task to run
    This may return None if there are either no tasks available or the maximum
    number of tasks are already executing for the testrun
    """
    task = None
    testrunactionid = None
    # Enter a transaction to guarantee any decision made is not invalidated
    # by other thread's actions

    ################################################
    # Timing critical code. Absolute minimum delay #
    ################################################
    rollback = True
    try:
      try:
        self.ovtDB.setAutoCommit(False)
        # Find if there is space for another task from this testrun
        # This TAKES A TESTRUN LOCK
        (max, used) = self.ovtDB.getTaskUsage(self.testrunid)
        # Need to double check the status of the testrun whilst holding the lock
        if self.ovtDB.getTestrunRunstatus(self.testrunid) in ("RUNNING",
                                                              "HOSTALLOCATED"):
          # Proceed to find a task if the testrun is still running
          if max > used:
            # Now find a task that can be run
            testrunactionids = self.ovtDB.getAvailableTestrunActions(self.testrunid)
            if len(testrunactionids) != 0:
              try:
                for testrunactionid in testrunactionids:
                  # Deferred execution slows down how frequently a task is considered
                  # for execution when it is waiting for resources
                  if testrunactionids[testrunactionid] == 1:
                    continue
                  if not self.ovtDB.checkHostMatch(testrunactionid, hostid):
                    continue
                  # mark the testrun as started so that if resource allocation
                  # causes a queue the testrun still appears to have started
                  # running, which is correct but it is just queued on resources
                  self.setStarted()
                  # Now acquire the resources required
                  if self.ovtDB.acquireResources(testrunactionid):
                    # Instantiate the task
                    self.ovtDB.registerExecutionHost(testrunactionid, hostid)
                    task = testrunactionid
                    break
              except (AllocationException, AllocationAbortException), ex:
                # Resource allocation is impossible for some reason...
                self.logHelper("Failed to allocate resources for %u"
                               % testrunactionid)
                (actionid, versionedactionid) = self.ovtDB.getTaskIdentifiers(testrunactionid)
                self.submit(actionid, False, {"__OVT_EXCEPT__":str(ex)})
                self.setAborting()
                task = None
            elif used == 0:
              # Nothing is running and nothing was available to run
              # The testrun is complete
              self.ovtDB.setTestrunRunstatus(self.testrunid, "COMPLETED")
  
        self.ovtDB.FORCECOMMIT()
        self.ovtDB.setAutoCommit(True)
        rollback = False
      except DatabaseRetryException:
        # Just do a reconnect. We will not have allocated a task as the
        # FORCECOMMIT must succeed before that happens and the exception cannot
        # be thrown after that.
        rollback = True
        task = None

    finally:
      if rollback:
        try:
          self.ovtDB.FORCEROLLBACK()
        except DatabaseRetryException:
          pass
    # Initialize the task outside of the critical section!
    if task != None:
      # This may be the first task to execute in this testrun.
      # Mark the testrun as running
      # On exception, try and abort the testrun first such that cascading
      # exceptions generally do not leave the testrun in an unstable state
      # Any unexpected exception in this block is an overtest bug.
      (actionid, versionedactionid) = self.ovtDB.getTaskIdentifiers(task)
      try:
        self.initResources(versionedactionid, testrunactionid)
        exec("from action.A%d import *" % actionid)
        exec("task = A%d((self, versionedactionid, testrunactionid, actionid))"
             % actionid)
        exec("del(sys.modules['action.A%d'])" % actionid)
      except ResourceInitFailedException, ex:
        if ex.isTransient ():
          # When a resource fails to initialise for a (potentially) transient
          # reason roll it back to pre-initialisation and pause the testrun to
          # allow a user to recover the resource and continue
          self.setPaused (lock = True)
          self.rewindTask (testrunactionid)
        else:
          self.setAborting (lock = True)
          self.setTaskEnded (testrunactionid)
        self.logHelper(str(ex))
        self.submit(actionid, False, {"__OVT_EXCEPT__":str(ex)})
        if ex.isTransient ():
          # Redo the rewind as the submission above will have set the passed flag
          # Keep the result submission below setPaused as exceptions during submit
          # can leave the system in a bad state
          self.rewindTask (testrunactionid)
        task = None
      except ImportError:
        self.setAborting(lock = True)
        self.setTaskEnded(testrunactionid)
        self.logHelper("Failed to import action.A%u" % actionid)
        self.submit(actionid, False, {"__OVT_EXCEPT__":
                                      "Failed to import action module\n%s"
                                      % formatExceptionInfo()})
        task = None
      except SyntaxError:
        self.setAborting(lock = True)
        self.setTaskEnded(testrunactionid)
        self.logHelper("Action.A%u has a syntax error" % actionid)
        self.submit(actionid, False, {"__OVT_EXCEPT__":
                                      "Syntax error in action module\n%s"
                                      % formatExceptionInfo()})
        task = None
      except Exception:
        self.setAborting(lock = True)
        self.setTaskEnded(testrunactionid)
        self.logHelper("Action.A%u has caused an unexpected exception" % actionid)
        self.submit(actionid, False, {"__OVT_EXCEPT__":
                                      "Exception in action module\n%s"
                                      % formatExceptionInfo()})
        task = None
    return task

  def getNextTaskToArchive(self, hostid):
    """
    Finds the next available task to archive
    This may return None if there are no tasks left to archive on this machine
    """
    task = None
    testrunactionid = None
    # Enter a transaction to guarantee any decision made is not invalidated
    # by other thread's actions

    ################################################
    # Timing critical code. Absolute minimum delay #
    ################################################
    rollback = True
    try:
      try:
        self.ovtDB.setAutoCommit(False)
        # Now find a task that can be archived (TAKES A TESTRUN LOCK)
        testrunactionids = self.ovtDB.getAvailableTestrunActionsToArchive(self.testrunid)
        # The testrun lock is now held but unlike normal task selection,
        # archiving cannot be interrupted unless it has finished in which case
        # there will be no testrunactionids returned anyway
        if len(testrunactionids) != 0:
          for testrunactionid in testrunactionids:
            match = self.ovtDB.checkTaskExecutedOnHost(testrunactionid, hostid)
            if match == False:
              continue
            self.ovtDB.setTaskArchiving(testrunactionid)
            task = testrunactionid
            break
        else:
          # There is nothing left to start running but not all jobs will be
          # complete, so don't do anything just yet
          None
  
        self.ovtDB.FORCECOMMIT()
        self.ovtDB.setAutoCommit(True)
        rollback = False
      except DatabaseRetryException:
        # Just do a reconnect. We will not have allocated a task as the
        # FORCECOMMIT must succeed before that happens and the exception cannot
        # be thrown after that.
        rollback = True
        task = None

    finally:
      if rollback:
        try:
          self.ovtDB.FORCEROLLBACK()
        except DatabaseRetryException:
          pass

    # Initialize the task outside of the critical section!
    if task != None:
      (actionid, versionedactionid) = self.ovtDB.getTaskIdentifiers(task)
      try:
        self.initResources(versionedactionid, testrunactionid, init=False)
        exec("from action.A%d import *" % actionid)
        exec("task = A%d((self, versionedactionid, testrunactionid, actionid))"
             % actionid)
        exec("del(sys.modules['action.A%d'])" % actionid)
      except ResourceInitFailedException, ex:
        self.logHelper("Archiver: %s"%str(ex))
        self.ovtDB.appendToResourceLog(hostid, "Archiver: %s" % str(ex))
        self.setTaskArchived(testrunactionid)
        task = None
      except ImportError:
        # In error conditions we sneak into the host log to report the error and
        # then mark the task as archived anyway
        # WORK NEEDED: This has the potential to leave junk around!
        self.logHelper("Archiver: Failed to import action.A%u" % actionid)
        self.ovtDB.appendToResourceLog(hostid,
                                       "Archiver: Failed to import action.A%u"
                                       % actionid, index=0)
        self.setTaskArchived(testrunactionid)
        task = None
      except SyntaxError:
        self.logHelper("Archiver: Action.A%u has a syntax error\n%s"
                       % (actionid, formatExceptionInfo()))
        self.ovtDB.appendToResourceLog(hostid, 
                                       "Archiver: Action.A%u has a syntax error\n%s"
                                       % (actionid, formatExceptionInfo()), 
                                       index=0)
        self.setTaskArchived(testrunactionid)
        task = None
      except Exception:
        self.logHelper("Archiver: Action.A%u has caused an unexpected exception\n%s"
                       % (actionid, formatExceptionInfo()))
        self.ovtDB.appendToResourceLog(hostid, 
                                       "Archiver: Action.A%u has caused an unexpected exception\n%s"
                                       % (actionid, formatExceptionInfo()),
                                       index=0)
        self.setTaskArchived(testrunactionid)
        task = None
    return task

  def getVersion(self, versionedactionidoractionname):
    if type(versionedactionidoractionname) in types.StringTypes:
      return self.ovtDB.getVersionInfoForAction (self.testrunid,
                                                 versionedactionidoractionname)
    else:
      return self.ovtDB.getVersionInfo(versionedactionidoractionname)

  def isDefaultDependency(self, consumeraction, produceraction):
    """
    Report if the versions of the consumer and producer in this testrun form
    a default dependency
    """
    versionedactionid = self.ovtDB.getVersionedActionFromTestrun(self.testrunid, consumeraction)
    if versionedactionid == None:
      return False
    versionedactiondep = self.ovtDB.getVersionedActionFromTestrun(self.testrunid, produceraction)
    if versionedactiondep == None:
      return False
    dependencies = self.ovtDB.getDependencies(versionedactionid)

    for group in dependencies:
      for action in dependencies[group]:
        for info in dependencies[group][action]:
          if info['versionedactionid'] == versionedactiondep:
            return info['defaultdep']
    return False

  def getSharedPath(self, versionedactionidoractionname):
    if type(versionedactionidoractionname) in types.StringTypes:
      versionedactionid = self.ovtDB.getVersionedActionFromTestrun(self.testrunid, versionedactionidoractionname)
      if versionedactionid == None:
        return None
    else:
      versionedactionid = versionedactionidoractionname

    return os.path.join(CONFIG.shareddir,str(self.getTestrunid()),
                        str(versionedactionid), "shared")

  def getTestsuite(self, actionid):
    """
    Find the testsuiteid for the specified action
    Returns None if actionid is not a testsuite
    """
    return self.ovtDB.getTestsuite(actionid)

  def setTaskEnded (self, testrunactionid):
    """
    Set the completeddate on the given task
    """
    self.ovtDB.setTaskCompleted(testrunactionid)
    self.ovtDB.releaseResources(testrunactionid)

  def rewindTask (self, testrunactionid):
    """
    Rewind the task state to pre-allocation
    """
    self.ovtDB.rewindTask (testrunactionid)

  def setTaskArchived (self, testrunactionid):
    """
    Set the archived flag
    """
    self.ovtDB.setTaskArchived(testrunactionid)

  def archiveComplete(self):
    """
    Determine if archiving is actually complete.
    Mark the testrun as archived if so, or delete it if deleting.
    """
    # Needs to determine if archiving or deleting is in progress and then move
    # to archived or delete it if all tasks are archived.

    success = False
    while not success:
      try:
        self.ovtDB.setAutoCommit(False)
        # First check if the testrun is fully archived
        if self.ovtDB.isTestrunArchived(self.testrunid):
          status = self.ovtDB.getTestrunRunstatus(self.testrunid)
          if status == "ARCHIVING":
            self.logHelper("Archive complete")
            self.ovtDB.setTestrunRunstatus(self.testrunid, "ARCHIVED")
          elif status == "DELETING":
            self.logHelper("Delete complete")
            self.ovtDB.DELETETESTRUN(self.testrunid)
        self.ovtDB.FORCECOMMIT()
        success = True
        self.ovtDB.setAutoCommit(True)
      except DatabaseRetryException:
        pass

  def submit(self, actionnameorid, result, extendedresults = None):
    """
    Fill in a test result for the given action, along with any extended results
    required
    WORK NEEDED: To optimise this function it should really be associate with an
                 action. i.e. not be situated at the testrun level but actually
                 at the action level and from there it should utilise the
                 actioncategory in order to remove the possibility of getting
                 duplicate action names.
    """
    if extendedresults == None:
      extendedresults = {}
    testrunactionid = self.ovtDB.findTestrunAction(actionnameorid, self.testrunid)
    if testrunactionid == None:
      raise ResultSubmissionException("Action: %s is not in testrun: %u"
                                      % (actionnameorid, self.testrunid))
    self.ovtDB.setResult(testrunactionid, result)
    # setExtendedResult requires a transaction as it must atomically
    # modify both the resultfield table as a whole and the specific
    # results for testrunactionid
    for field in extendedresults:
      success = False
      while not success:
        try:
          self.ovtDB.setAutoCommit(False)
  
          self.ovtDB.setExtendedResult(testrunactionid, field,
                                       extendedresults[field])
          self.ovtDB.FORCECOMMIT()
          success = True
          self.ovtDB.setAutoCommit(True)
        except DatabaseRetryException:
          pass

    return True

  def actionQuery(self, actionname):
    """
    Fetch a dictionary describing an action's result
    """
    return self.ovtDB.getActionResult (self.testrunid, actionname)

  def testsuiteQuery(self, testsuiteid, tests = None, options = None):
    """
    Fetch a dictionary describing a test's result
    Options allow various inference techniques to be applied to find a test
    result
    """
    if not self.ovtDB.verifyTestsuiteInTestrun (self.testrunid, testsuiteid):
      raise ResultSubmissionException("Testsuite: %s is not in testrun: %u"
                                      % (testsuiteid, self.testrunid))

    if options == None:
      options = {}
    if tests == None:
      tests = {}
    
    results = self.ovtDB.getTestResult (self.testrunid, tests=tests,
                                        testsuiteid=testsuiteid,
                                        options=options)
    if 'clone_result' in options and options['clone_result']:
      for test in results:
        if 'inferredfrom' in results[test] and 'inferred' in results[test]:
          passStatus = results[test]['pass']
          if passStatus == None:
            passStatus = True
          self.testsuiteSubmit(testsuiteid,
                               test,
                               passStatus,
                               version=results[test]['version'],
                               inferredfrom=results[test]['inferredfrom'])

    return results

  def testsuiteSubmit(self, testsuiteid, testnameorid, result,
                      extendedresults = None, version = "1.0",
                      inferredfrom = None):
    """
    Submit a result for a test in a testsuite.
    testsuiteid is the id for the testsuite.
    The testname is the name of a new or existing action in the testsuite.
    The testid is an existing action (that must be in the testsuite)

    The action relating to testsuiteid must be present in the testrun to 
    submit results for tests in the testsuite.

    The testnameorid for the test may or may not already be part of the
    testrun and is added as required

    The result is set when adding the test to the testrun or updated if
    already existing

    The extended result data is added to the test results too. The fields for
    extended results are shared between all tests in a testsuite. Variables with
    the same name must have the same type. (This restriction may be relaxed over
    time as required)
    """
    if extendedresults == None:
      extendedresults = {}

    if not self.ovtDB.verifyTestsuiteInTestrun (self.testrunid, testsuiteid):
      raise ResultSubmissionException("Testsuite: %s is not in testrun: %u"
                                      % (testsuiteid, self.testrunid))

    vtid = self.ovtDB.findOrCreateTestsuiteTest (testsuiteid, testnameorid,
                                                 version)

    testruntestid = self.ovtDB.findOrAddTestsuiteTestToTestrun (self.testrunid, vtid)

    self.ovtDB.setTestResult (testruntestid, result, inferredfrom=inferredfrom)
    # setTestExtendedResult requires a transaction as it must atomically
    # modify both the resultfield table as a whole and the specific
    # results for testrunactionid
    for field in extendedresults:
      success = False
      while not success:
        try:
          self.ovtDB.setAutoCommit(False)
  
          self.ovtDB.setTestExtendedResult (testruntestid, field,
                                            extendedresults[field])
          self.ovtDB.FORCECOMMIT()
          success = True
          self.ovtDB.setAutoCommit(True)
        except DatabaseRetryException:
          pass

    return True

class TestConfig:
  def __init__(self, testrun, versionedactionid):
    self.ovtDB = testrun.ovtDB
    self.testrun = testrun
    self.versionedactionid = versionedactionid

  def getVariable(self, name):
    """
    Return the value for a given option.
    An exception will be raised if the option either does not exist or is not
    linked to the current versioned action.
    """
    variable = self.ovtDB.getConfigSetting(self.testrun.getTestrunid(),
                                           self.versionedactionid, name)
    if variable != None:
      return variable
    else:
      raise ConfigException("%s variable not found" % (name))

  def setVariable(self, name, value):
    """
    Set the value of a given option.
    An exception will be raised if:
    1) The option either does not exist.
    2) Is not linked to the current versioned action.
    3) If the type of value does not match the type of the option.
    4) The option is not an automatic variable
    """
    if not self.ovtDB.setConfigSetting(self.testrun.getTestrunid(),
                                       self.versionedactionid, name, value):
      raise ConfigException("%s variable not found" % (name))


