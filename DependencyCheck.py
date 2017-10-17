import time
import Dependencies
import signal
import types
from OvertestExceptions import *
from LogManager import LogManager

class DependencyCheck:
  """
  Analyse a testrun to verify the dependencies
  This will also pull in any dependencies that can automatically be solved
  """
  def __init__(self, ovtDB, log = True):
    self.ovtDB = ovtDB
    self.dependencies = Dependencies.Dependencies(ovtDB)
    self.log = None
    if log:
      self.log = LogManager("dependency_check", True)

  def termhandler(self, signum, frame):
    """
    Handle SIGTERM gracefully
    """
    self.quit = True

  def run(self):
    """
    Find all testruns ready for checking and do the analysis
    """
    self.quit = False
    signal.signal(signal.SIGTERM, self.termhandler)
    try:
      while not self.quit:
        testrunids = self.ovtDB.getTestrunsToCheck()
  
        for testrunid in testrunids:
          self.testrunid=testrunid
          self.notify("Checking testrun")
          result = self.checkTestrun (testrunid, self.notify)
          if result == True:
            # Success
            self.notify("Checked")
	    trinfo = self.ovtDB.simple.getTestrunById(testrunid)

	    if trinfo['usegridengine']:
              self.ovtDB.setTestrunRunstatus(testrunid, 'CHECKEDGRID')
	    else:
              self.ovtDB.setTestrunRunstatus(testrunid, 'CHECKED')
          else:
            # An error
            self.ovtDB.setTestrunRunstatus(testrunid, 'CHECKFAILED')

        time.sleep(5)
    except KeyboardInterrupt, e:
      None

  def notify(self, message):
    """
    Log a message
    """
    self.log.write("TR%u: %s"%(self.testrunid, message))

  def checkTestrun(self, testrunid, notify):
    """
    Perform all dependency checks for a testrun
    Return True on success
    Return a string representing an error otherwise
    """
    versionedactioniddict = self.ovtDB.getVersionedActionidDict(testrunid)
  
    try:
      vaids = set(versionedactioniddict.keys())
  
      if self.dependencies.resolveDependencies(versionedactioniddict) == None:
        notify("There are dependencies that cannot be automatically resolved")
        return False
      else:
        newvaids = set(versionedactioniddict.keys())
        addthese = newvaids-vaids
  
        for vaid in addthese:
          self.ovtDB.addToTestrun(testrunid, vaid, autodependency=True)

        # Verify that auto dependency analysis has not resulted in
        # multiple versions of any action being included. This can happen
        # when multiple versioned actions depend on different distinct
        # subsets of versions of another action.
        duplicates = self.ovtDB.checkSingleActionPerTestrun(testrunid)

        if len(duplicates) != 0:
          notify("Multiple versions of the same action are now in this testrun") 
          for duplicate in duplicates:
            notify("'%s' has %u versions" % (duplicate, duplicates[duplicate]))
          return False

        # Categories, actions and versions can be marked as invalid when they can
        # not be used any more. This is usually because of external dependencies
        # no longer being fulfilled but may be because the maintenance work in
        # module code makes them too hard to support
        invalidversions = self.ovtDB.checkValidVersionedActionsInTestrun(testrunid)
        
        if len(invalidversions) != 0:
          notify("Invalid versioned actions included in testrun")
          for invalid in invalidversions:
            notify("%s is invalid" % invalid)
          return False

        # Sanitize the configuration to ensure that all options have settings
        # and remove all settings that have no linked option.
        configerrors = self.ovtDB.sanitizeConfigSettings(testrunid)

        if len(configerrors) > 0:
          notify("Illegal Config Option Lookups selected:")
          for configerror in configerrors:
            notify("%s:%s:%s is invalid" % (configerror['configoptiongroupname'], configerror['configoptionname'], configerror['lookupname']))
          return False

        return True
  
    except ImpossibleDependencyException, e:
      notify(str(e))
      return False
