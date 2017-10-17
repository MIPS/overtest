import os

from Execute import Execute
from OvertestExceptions import *
from Config import CONFIG
from OvtDB import OvtDB

class Resource(Execute):
  """
  Handle access to and initialisation of a resource
  """
  def __init__(self, data):
    """
    Initialise the resource
    """
    Execute.__init__(self)
    if isinstance(data, OvtDB):
      self.ovtDB = data
      return

    if data == None:
      return

    (_testrun, identifier, data) = data
    self.testrun = _testrun
    self.logdir = None
    if 'versionedactionid' in identifier:
      self.userclaimid = None
      self.versionedactionid = identifier['versionedactionid']
    else:
      self.versionedactionid = None
      self.userclaimid = identifier['userclaimid']
      if 'logdir' in identifier:
        self.logdir = identifier['logdir']

    # Accumulate errors so that they can be retrieved if required
    self.errors = ""

    self.proccount = 0
    self.archiveMode = False

    self.attributes = data['attributes']
    self.requestedattributes = data['requested']
    self.name = data['name']
    self.hostname = data['hostname']
    self.resourceid = data['resourceid']
    self.type = data['type']
    self.typeid = data['typeid']
    self.localpath = None
    self.logpath = None
    self.umask = 007

  def getResourceid(self):
    return self.resourceid

  def getAttributes(self):
    return self.attributes

  def getPrefix(self):
    """
    The prefix for resource log files
    """
    return "r%d."%(self.typeid)

  def getLogPath(self):
    """
    Get the overtest allocated shared path
    OR
    the local path for manual claims
    """
    if self.logpath == None:
      if self.versionedactionid != None:
        self.logtestrunpath = os.path.join(CONFIG.logdir,str(self.testrun.getTestrunid()))
        self.logpath = os.path.join(self.logtestrunpath, str(self.versionedactionid))
        if not self.createDirectory(self.logpath):
          self.logpath = None
      else:
        # For manual claims local and log file paths are the same
        self.logpath = self.getLocalPath()

    return self.logpath

  def getLocalPath(self):
    """
    Get the overtest allocated local path
    """
    if self.localpath == None:
      if self.versionedactionid != None:
        self.localtestrunpath = os.path.join(CONFIG.localdir,
                                             str(self.testrun.getTestrunid()))
        self.localpath = os.path.join(self.localtestrunpath, str(self.versionedactionid))
      else:
        # Use the logdir for the local workspace as well as log path
        if self.logdir != None:
          self.localpath = os.path.join(self.logdir, str(self.userclaimid))
        else:
          self.localpath = os.path.join(os.path.expanduser("~"),
                                        ".overtest", str(self.userclaimid))
      # Create the local overtest area
      success = self.createDirectory(self.localpath)
      if not success:
        self.localpath = None
    return self.localpath

  def getWorkPath(self):
    """
    Get the work path for resource initialisation commands
    """
    return os.path.join(self.getLocalPath(), "res%d"%self.typeid)

  def updateEnvironment(self, env):
    """
    Make any automated environment changes
    """
    # There are no changes for resources
    None

  def logHelper(self, string):
    """
    Add a log message, prepended with this resource's identifier
    """
    self.testrun.logHelper("r%u: %s" % (self.resourceid, string))

  def processStarted(self, process):
    """
    Perform any required actions just after a process starts
    """
    # Resources do not do anything special
    None

  def error(self, message, transient = False):
    """
    Register an error
    """
    # WORK NEEDED: register the error properly
    self.errors += "%s\n"%message
    self.logHelper("ERROR: %s"% message)

    raise ResourceInitFailedException("%s resource failed to initialise\n%s\nCheck logs (%s) for further details."
                                      % (self.name, self.errors, self.getLogPath()), transient=transient)

  def transientError (self, message):
    """
    Register a transient error
    This will result in the task being descheduled
    Task status will be rolled back and the testrun paused
    """
    self.error (message, transient = True)

  def initialiseChecked(self):
    """
    Initialise the resource with error checking
    """
    self.proccount = 0
    self.logHelper("Initialising: %s" % self.name)
    result = False
    try:
      result = self.initialise()
    except (ResourceException), e:
      self.error(str(e))
      result = False
    except KeyboardInterrupt, e:
      self.error("Initialise interrupted")
      raise

    if not result:
      self.error ("Resource initialisation failure without error message")

    return result

  def getType(self):
    """
    Return the type of the resource
    """
    return self.type

  def getName(self):
    """
    Return the name of the resource
    """
    return self.name

  def getHostName(self):
    """
    Return the hostname for the resource
    """
    return self.hostname

  def query(self, args):
    """
    Allow Resource information to be queried.

    The result of the query depends on the information being
    queried. For example, querying an 'attribute' of a Resource
    returns that attribute's value.
    """
    query_type = args[0]

    if query_type == "-a":
      # attribute
      attr = args[1]
      attrs = self.getAttributeValues(attr)
      for a in attrs[1]:
        print attrs[0][a]['data']

    else:
      print "ERROR: Unknown query type"
      return 1

  def getAttributeValues(self, name):
    """
    Return the set of values supported by an attribute
    """
    # If this object was created with a database connection we query
    # the database for all possible values of attribute "name".
    if hasattr(self, "ovtDB"):
      return self.ovtDB.getAttributesByName(self.RESOURCETYPEID, name)

    if name in self.attributes:
      return self.attributes[name]
    else:
      raise ResourceException(self.name +" has no attribute "+name)

  def getAttributeValue(self, name):
    """
    Return the value of an attribute iff there is only one possibility
    """
    if name in self.attributes and len(self.attributes[name]) == 1:
      return self.attributes[name][0]
    else:
      raise ResourceException(self.name+" has no unique value for attribute "+name)

  def getRequestedAttributeValues(self, name):
    """
    Returns the attribute values that were actually requested rather than
    what a resource has
    """
    if name in self.requestedattributes:
      return self.requestedattributes[name]
    else:
      raise ResourceException(self.name +" has no attribute "+name)

  def getRequestedAttributeValue(self, name):
    """
    Returns the attribute value that were actually requested rather than
    what a resource has
    """
    if name in self.requestedattributes and len(self.requestedattributes[name]) == 1:
      return self.requestedattributes[name][0]
    else:
      raise ResourceException(self.name +" has no unique value for attribute "+name)
