import os
import subprocess
import sys
import time
import random
import gzip

from Config import CONFIG
from Execute import Execute
from OvertestExceptions import *

class Action(Execute):
  """
  Abstract class used to implement all actions. The minimum that a derived
  class must implement is the :py:meth:`~.Action.run` method. The
  :py:meth:`~.Action.archive` method should be overridden when derived
  files are stored outside the working area. The
  :py:meth:`~.Action.formatResults` method should be overridden for
  customised results formatting in email notifications.
  """

  debug_verbose = 0

  def __init__(self, (_testrun, _versionedactionid, _testrunactionid, actionid)):
    """
    Set up the environment for running this action for the given testrun
    """
    Execute.__init__(self)
    self.testrun = _testrun
    self.versionedactionid = _versionedactionid
    self.testrunactionid = _testrunactionid
    self.localpath = None
    self.logpath = None
    self.logtestrunpath = None
    self.sharedpath = None
    self.sharedtestrunpath = None
    self.actionid = actionid
    self.concurrency = 1
    self.multiresults = {}

    # Grab the config for this action
    self.config = self.testrun.getConfig(self.versionedactionid)
    # Get the version string
    self.version = self.testrun.getVersion(self.versionedactionid)
    # Find out if this is a testsuite
    self.testsuiteid = self.testrun.getTestsuite(actionid)
    self.submissionid = None

  def warn(self, message):
    """
    Raise a warning and store it in the logs

    :param message: The warning message
    :type message: string
    """
    self.logHelper("WARN: %s" % message)

  def error(self, message, exception=True):
    """
    Raise an error and store it in the logs. Also submit it as an extended
    result when reported during the :py:meth:`~.Action.run` method. Normally
    throws an exception which is caught by the framework.

    :param message: The error message
    :type message: string
    :param exception: Specifies if an exception should be thrown, default
                      enabled
    :type exception: boolean
    :return: False or raises TaskRunErrorException
    :rtype: boolean
    """
    self.logHelper("ERROR: "+message)
    if not self.archiveMode:
      self.testrun.submit(self.actionid, False, {"Error":message})

    if exception:
      raise TaskRunErrorException(actionid = self.actionid)

    return False

  def success(self, extendedresults=None):
    """
    Report successful execution along with any additional result data

    :param extendedresults: Field-value pairs of extra result information.
                            Float, integer, boolean and string types are
                            supported
    :type extendedresults: dictionary
    :return: True - normally used in the :py:meth:`~.Action.run` method as
             "return self.success()"
    :rtype: boolean
    """
    self.testrun.submit(self.actionid, True, extendedresults)
    return True

  def failure(self, extendedresults=None):
    """
    Report failed execution along with any additional result data

    :param extendedresults: Field-value pairs of extra result information.
                            Float, integer, boolean and string types are
                            supported
    :type extendedresults: dictionary
    :return: False - normally used in the :py:meth:`~.Action.run` method as
             "return self.failure()"
    :rtype: boolean
    """
    self.testrun.submit(self.actionid, False, extendedresults)
    return False

  def testsuiteSubmit(self, testnameorid, result, extendedresults=None, version = None):
    """
    Submit a result for a test in the current action's testsuite

    :param testnameorid: The name of the test or action identifier
    :type testnameorid: string or integer
    :param result: Specifies if the test passed
    :type result: boolean
    :param extendedresults: Field-value pairs of extra result information.
                            Float, integer, boolean and string types are
                            supported
    :type extendedresults: dictionary
    :param version: Version of test, defaults to 1.0
    :type version: string
    :return: False when action is not a testsuite, otherwise True
    :rtype: boolean
    """
    if self.testsuiteid == None:
      return False

    if version == None:
      self.testrun.testsuiteSubmit(self.testsuiteid, testnameorid, result, extendedresults)
    else:
      self.testrun.testsuiteSubmit(self.testsuiteid, testnameorid, result, extendedresults, version)

    return True

  def testsuiteQuery(self, tests = None, options = None):
    """
    Fetch results for one or more tests in the current action's testsuite
    
    :param tests: test name -> version pairs to query. Version can be None or
                  tests==None returns all available results
    :type tests: dictionary or None
    :param options: Options controlling results query:

                    * **use_simple_equivalence** - (*boolean*) Finds results from
                      other testruns that match the versions of tests explicitly
                      specified. The simple equivalence applies to the testsuite
                      action. Version information must fully identify an
                      instance of a test for this feature to be useful (i.e. it
                      is a checksum of the test).
                    * **clone_result** - (*boolean*) Copies results from other
                      testruns when using simple equivalences
    :type options: dictionary
    :return: False when not a testsuite otherwise a dictionary as below
    :rtype: False or dictionary

    The dictionary returned from this method has the following structure::

      { 'test_name' : { 'version' : version_name,
                        'pass'    : overall_success,
                        'extended': { 'field' : value... } } }
    """
    if self.testsuiteid == None:
      return False
    return self.testrun.testsuiteQuery(self.testsuiteid, tests, options)

  def actionQuery(self):
    """
    Fetch results associated with this action

    :return: A dictionary structured as below
    :rtype: dictionary

    The dictionary returned from this method has the following structure::

      { 'version' : version_name,
        'pass'    : overall_success,
        'extended': { 'field' : value... } } }
    """
    return self.testrun.actionQuery(self.name)

  def logHelper(self, string):
    """
    Add a log message, prepended with this actions identifier
    """
    self.testrun.logHelper("A%u(V%u): %s" % (self.actionid, self.versionedactionid, string))

  def getSharedPath(self, nocreate=False):
    """
    Get the overtest allocated shared path
    """
    if self.sharedpath == None:
      self.sharedtestrunpath = os.path.join(CONFIG.shareddir,str(self.testrun.getTestrunid()))
      self.sharedpath = os.path.join(self.sharedtestrunpath, str(self.versionedactionid), "shared")

      if nocreate and not os.path.exists(self.sharedpath):
        self.sharedpath = None
        return False

      # Create the shared overtest area
      success = self.createDirectory(self.sharedpath)
      if not success:
        self.sharedpath = None
    
    return self.sharedpath

  def getLogPath(self):
    """
    Get the overtest allocated log file path
    """
    if self.logpath == None:
      self.logtestrunpath = os.path.join(CONFIG.logdir,str(self.testrun.getTestrunid()))
      self.logpath = os.path.join(self.logtestrunpath, str(self.versionedactionid))

      # Create the log area
      success = self.createDirectory(self.logpath)
      if not success:
        self.logpath = None
    
    return self.logpath

  def getLocalPath(self, nocreate=False):
    """
    Get the overtest allocated local path
    """
    if self.localpath == None:
      self.localtestrunpath = os.path.join(CONFIG.localdir,
                                           str(self.testrun.getTestrunid()))
      self.localpath = os.path.join(self.localtestrunpath, str(self.versionedactionid))

      if nocreate and not os.path.exists(self.localpath):
        self.localpath = None
        return False

      # Create the local overtest area
      success = self.createDirectory(self.localpath)
      if not success:
        self.localpath = None
    return self.localpath

  def getWorkPath(self, nocreate=False):
    """
    Get the working directory allocated to this action

    :param nocreate: Controls whether to create the folder if it does not exist
    :type nocreate: boolean
    :return: Absolute path of the working area or False if nocreate and the folder
             does not already exist
    :rtype: path
    """
    if nocreate and self.getLocalPath(nocreate=True) is False:
      return False

    workpath = os.path.join(self.getLocalPath(), "work")
    if nocreate and not os.path.exists(workpath):
      return False

    self.createDirectory(workpath)
    return workpath

  def getTMPPath(self, nocreate=False):
    """
    Get the temporary directory allocated to this action

    :param nocreate: Controls whether to create the folder if it does not exist
    :type nocreate: boolean
    :return: Absolute path of the temp area or False if nocreate and the folder
             does not already exist
    :rtype: path
    """
    if nocreate and self.getLocalPath(nocreate=True) is False:
      return False

    tmppath = os.path.join(self.getLocalPath(), "tmp")
    if nocreate and not os.path.exists(tmppath):
      return False

    self.createDirectory(tmppath)
    return tmppath


  def registerLogFile (self, filename, compress = False):
    """
    Register a log file for permanent storage. I.e. it is not subject to removal on archive.

    :param filename: The file to register
    :type filename: path
    :return: True when the file is successfully registered
    :rtype: boolean
    """
    if not os.path.exists(filename):
      return False

    fname = os.path.basename (filename)
    if fname == "":
      return False
    try:
      if not compress:
	os.system ("cp \"%s\" \"%s\""%(filename, os.path.join(self.getLogPath(), "log.%s"%fname)))
      else:
	f_in = open(filename, 'rb')
	f_out = gzip.open(os.path.join(self.getLogPath(), "log.%s.gz"%fname), 'wb')
	f_out.writelines(f_in)
	f_out.close()
	f_in.close()
    except OSError:
      return False
    return True

  def archive(self):
    """
    This will be called during archive or delete and should clean up any
    derived files stored outside of the working area. The framework will
    clean up the working area automatically.
    """
    pass

  def run(self):
    """
    Virtual method, must be overridden.

    This will be called to perform the work of an action. Any requested
    resources will have been claimed and initialised. Information relating to
    the specific instance of the action can be accessed through several helper 
    methods and attributes.

    * Action configuration information via the :py:attr:`.config` attribute.
    * Allocated resources via the :py:meth:`~.Action.getResource` method.
    * Version information via the :py:meth:`~.Action.getVersion` method.

    :returns: True if the action has completed sufficiently such that its
              consumers can execute
    :rtype: boolean
    """
    None

  # Execute the action.
  def gitFetch(self, reponame, deep=False):
    """
    The generic logic to clone a branch from a GIT repo
    """
    branch = self.config.getVariable(self.name + " Branch")
    remote = self.config.getVariable(self.name + " Remote")
    gitCmd = [CONFIG.git, "clone",
              ("--reference=%s/" % CONFIG.gitref) + reponame,
              "-b", branch]
    if not deep:
      gitCmd = gitCmd + ["--depth", "1"]
    gitCmd = gitCmd + [remote, self.name.lower()]

    if not os.path.exists (os.path.join(self.getSharedPath(), self.name.lower())):
      # Execute a command overriding some environment variables
      for i in range(30):
        result = self.execute(workdir=self.getSharedPath(),
			      command=gitCmd)
        if result == 0:
	  break
        else:
	  time.sleep(random.randint(1,30))
      if result != 0:
        self.error("Unable to clone repository")

    result = self.execute(workdir=os.path.join(self.getSharedPath(), self.name.lower()),
			  command=[CONFIG.git, "config", "core.preloadIndex", "false"])

    result = self.execute(workdir=os.path.join(self.getSharedPath(), self.name.lower()),
	                  command=[CONFIG.git, "rev-parse", "HEAD"])
    if result == 0:
      self.config.setVariable(self.name + " rev", self.fetchOutput().strip())

    return self.success()

  def getVersion(self, actionname=None):
    """
    Get the version of an action included in the current testrun

    :param actionname: The action to search for, default is None which
                       returns the current action's version
    :type actionname: string or None
    :return: Version number if action was found or None
    :rtype: string or None
    """
    if actionname == None:
      return self.version
    else:
      return self.testrun.getVersion(actionname)

  def runChecked(self):
    """
    Handles exceptions during execution
    """
    self.archiveMode = False
    self.proccount = 0
    self.logHelper("Running: %s" % self.name)
    result = False
    try:
      if self.testsuiteid != None:
        self.submissionid="%u:%u:%u"%(self.testrun.getTestrunid(), self.testsuiteid, self.testrun.getHostPID())
      result = self.run()
    except (ResourceException, ConfigException), e:
      self.error(str(e))
    except KeyboardInterrupt, e:
      self.error("Run interrupted", exception=False)
      raise

    if not result:
      self.error ("Task failure without error message")

    return result

  def archiveChecked (self, delete):
    """
    Placeholder for removing all files created but not needed to analyse results
    If delete is set then delete the results too
    """
    self.archiveMode = True
    self.proccount = 0
    self.logHelper("Archiving: %s" % self.name)
    result = False
    try:
      result = self.archive()
      # Delete the work directory, this is a local path
      if self.getWorkPath(nocreate=True) is not False:
        self.execute(workdir="/tmp", command=["rm", "-rf", self.getWorkPath()])
        # Try to delete the top level local directory
        try:
          os.rmdir(self.localtestrunpath)
        except OSError:
          # Just ignore it if it fails
          None

      # Delete the temp directory, this is a local path
      if self.getTMPPath(nocreate=True) is not False:
        self.execute(workdir="/tmp", command=["rm", "-rf", self.getTMPPath()])
        # Try to delete the top level local directory
        try:
          os.rmdir(self.localtestrunpath)
        except OSError:
          # Just ignore it if it fails
          None

      # Delete the shared area
      if self.getSharedPath(nocreate=True):
        self.execute(workdir="/tmp", command=["rm", "-rf", self.getSharedPath()])
        # Try to delete the top level shared directory
        try:
          os.rmdir(self.sharedtestrunpath)
        except OSError:
          # Just ignore it if it fails
          None

      if delete:
        # Delete the local area
	if self.getLocalPath(nocreate=True) is not False:
          self.execute(workdir="/tmp", command=["rm", "-rf", self.getLocalPath()])
          # Try to delete the top level log directory
          try:
            os.rmdir(self.localtestrunpath)
          except OSError:
            # Just ignore it if it fails
            None

        # Delete the log area
        try:
	  subprocess.call(["rm", "-rf", self.getLogPath()])
	except OSError:
          # Just ignore it if it fails
	  None

        # Try to delete the top level log directory
        try:
          os.rmdir(self.logtestrunpath)
        except OSError :
          # Just ignore it if it fails
          None

    except KeyboardInterrupt, e:
      self.error("Archive Interrupted", exception=False)
      raise
    return result

  def updateEnvironment(self, env):
    """
    Update env with Action specific settings
    """
    # Add the 'secret' submission id for testsuites to use with the
    # OvertestResult script
    if self.submissionid != None:
      env['__OVERTEST_SUBMISSION_ID__'] = self.submissionid
      env['PATH'] = sys.path[0]+":"+env['PATH']
      env['TMPDIR'] = self.getTMPPath()

  def getPrefix(self):
    """
    Get the log file prefix
    """
    prefix = ""
    if self.archiveMode:
      prefix = "a"
    return prefix

  def processStarted(self, process):
    """
    Store the PID of the new process
    """
    # At all times the PID stored in the database is the current or last process executed
    self.testrun.registerPID(self.versionedactionid, process.pid)

  def formatResults(self):
    """
    This will be called to produce an HTML formatted results page showing one
    set of results. A default generic implementation is provided but can be
    overridden.

    :return: HTML representing the results
    :rtype: string
    """
    import cgi
    output = ""
    results = self.actionQuery()
    output += "<b>Result Summary</b><br />"
    if results is None:
      output += "No summary information found"
    else:
      output += "<table>\n"
      output += "<tr><th>Field</th><th>Result</th></tr>\n"
      output += "<tr><th>Action passed</th>"
      if results['pass']:
        output += "<td style=\"background-color:green\">PASS</td>"
      else:
        output += "<td style=\"background-color:red\">FAIL</td>"
      output += "</tr>\n"
      for field in results['extended']:
        output += "<tr><th>%s</th>" % cgi.escape(field)
        value = results['extended'][field]
        output += "<td>%s</td></tr>\n" % (value)
      output += "</table>\n"
      output += "<br />\n"

    results = self.testsuiteQuery()
    if len(results) == 0:
      output += "No results submitted for this testsuite"
    else:
      output += "<table>\n"
      output += "<tr><th>Test:Version</th><th>Result</th>"

    testnames = results.keys()
    testnames.sort()

    extendedfields = []
    for test in testnames:
      if 'extended' in results[test]:
        for field in results[test]['extended']:
          if not field in extendedfields:
            extendedfields.append(field)
            output += "<th>%s</th>" % cgi.escape(field)

    output += "</tr>\n"

    for test in testnames:
      if results[test]['version'] != "1.0":
        testname = "%s:%s" % (test, results[test]['version'])
      else:
        testname = test
      output += "<tr><td>%s</td>" % (testname)
      if results[test]['pass']:
        output += "<td style=\"background-color:green\">PASS</td>"
      else:
        output += "<td style=\"background-color:red\">FAIL</td>"
      
      for field in extendedfields:
        value = "N/A"
        if field in results[test]['extended']:
          value = results[test]['extended'][field]
        output += "<td>%s</td>" % (value)

      output += "</tr>\n"

    output += "</table>\n"

    return output

  def addMultiResults(self, testrunid, results):
    """
    Store the set of results for future processing via formatMultiResults
    """
    self.multiresults[testrunid] = results

  def formatMultiResults(self, html = True):
    """
    Works similarly like formatResults(). However, it creates only a summary,
    it handles a list of results and combines them together.
    The function expects that each entry in results was fetched using
    actionQuery().
    """

    # 1) Fetch relevant results from resultsList and create dictonary
    resDict = {}
    actionFailList = []
    actionFormatErrList = []
    rowTitles = [] 

    for testrunid in self.multiresults:
      result = self.multiresults[testrunid]
      if not "pass" in result:
        actionFormatErrList.append(result)
        continue

      # combine results from actions which passed
      if result["pass"] == False:
        actionFailList.append(result)
        continue

      columnName = str(testrunid)

      if "heading" in result:
        columnName = result["heading"]

      resDict[columnName] = {}
      for fieldName in result["extended"]:
        if not fieldName in rowTitles:
          rowTitles.append(fieldName)
        resDict[columnName][fieldName] = result["extended"][fieldName]

    overallStatus = "PASS"
    if len(actionFailList) > 0:
      overallStatus = "FAIL"

    # 2) Put data into rows / columns appropriately
    table = []

    #  a) Create heading line
    headLine = [""]

    for columnName in resDict:
      headLine.append(columnName)

    table.append(headLine)
    
    #  b) Insert rows
    for rowTitle in rowTitles:
      line = [rowTitle]
      
      for columnName in resDict:
        if rowTitle in resDict[columnName]:
          line.append(str(resDict[columnName][rowTitle]))
        else:
          line.append("-")
      table.append(line)


    # 3) Format data
    output = ""

    if not html:
      output += "%s\n" % self.name
      output += "action status: %s" % overallStatus

      for row in table:
        output += "\n"
        output += str(row).strip("[]")
    else:
      output += "<h3> %s </h3>\n" % self.name
      output += "action status: %s" % overallStatus

      output += "\n<table border=\"1\">\n"
      for row in table:
        output += "<tr>\n"
        for entry in row:
          output += "<td> %s </td>" % str(entry)
        output += "\n</tr>\n"
      output += "</table>\n"

    if len(actionFailList) > 0:
      output += " - number of failed actions: %d" % len(actionFailList)

    if len(actionFormatErrList) > 0:
      output += " - number of formatting errors: %d" % len(actionFormatErrList)
      for err in actionFormatErrList:
        output += "   %s\n" % err

    return output
