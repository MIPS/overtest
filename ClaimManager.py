"""
Manual Claim Management Module
"""

from OvertestExceptions import ClaimReturnedException, DatabaseRetryException
from OvertestExceptions import AllocationException, AllocationAbortException
from OvertestExceptions import ResourceInitFailedException, formatExceptionInfo
from OvertestExceptions import NoQueueException, TimeoutException

from LogManager import LogManager
from DevelopmentHarness import DevTestrun
from utils.TerminalUtilities import bold
from postgresql.exceptions import UniqueError
import sys
import time
import getopt
import getpass

class ClaimManager:
  """
  Class to provide command line manual claim control
  """
  def __init__(self, ovtDB):
    """
    Resource claiming system
    """
    self.ovtDB = ovtDB
    self.log = LogManager(None, True)
    self.ovtDB.registerLog(self.log)
    self.debug = False
    self.globals = {}
    self.userclaimid = None

  def usage(self, exitcode, error = None, full=False):
    """
    Display the usage
    """
    if error != None:
      self.error(error)
      print ""
    print "Usage:"
    print "ClaimResource <no mode> "
    print "              Claim a (set of) resource(s)"
    print "ClaimResource -d --disclaim"
    print "              Return a (set of) resource(s)"
    print "ClaimResource -l --list"
    print "              List active resource requests"
    print "ClaimResource -f --fetch"
    print "              Fetch information about an allocation. This will be"
    print "              presented in YAML format unless a single attribute is"
    print "              requested"
    print "ClaimResource -h --help"
    print "              Show this help"
    print "ClaimResource --help-full"
    print "              Show this help with full option information"
    if full:
      print ""
      print "Options for all modes:"
      print "-c <claimnumber> --claim-id=<claimnumber>"
      print "              Specify the claim to make, cancel or list. When listing a"
      print "              specific claim, more information is provided"
      print "-u <username> --user=<username>"
      print "              Specify the user to impersonate. This should be"
      print "              auto-detected from your login shell"
      print "--logdir=<directory>"
      print "              Specify the location to write log files to. This will"
      print "              default to ~/.overtest/. Logs for each claim will be"
      print "              written to a directory named as the claim id"
      print ""
      print "Options for claiming resources:"
      print "-t <typename> --type=<typename>"
      print "              Specify the type of resource to claim. At least one must be"
      print "              specified"
      print "-a <attributename> --attribute=<attributename>"
      print "              All types must be followed by at least one attribute"
      print "-v <value> --value=<value>"
      print "              All attributes must be followed by at least one value"
      print "-r <reason> --reason=<reason>"
      print "              All resource requests must have a reason"
      print "-w --wait"
      print "              Do not return until the request succeeds. The request will"
      print "              be cancelled if the script is terminated"
      print "--timeout <timeout in minutes>"
      print "              Wait for a resource but quit after a certain length of time"
      print "-s <command> --shell <command>"
      print "              If the resource request is successful start a new shell"
      print "              and execute the command. -s must be the last option and"
      print "              when the shell closes the resources will be released"
      print ""
      print "Options for listing resources:"
      print "--all"
      print "              Show all requests by all users"
      print ""
      print "Options for fetching allocation information"
      print "-t <typename> --type=<typename>"
      print "              Specify the type of resource to get info for. Exactly one"
      print "              must be specified"
      print "-a <attributename> --attribute=<attributename>"
      print "              If only one attribute is requested it will emitted directly"
 
    sys.exit(exitcode)

  def error(self, error):
    """
    Print an error message
    """
    sys.stderr.write("ERROR: %s\n" % error)

  def execute(self, args):
    """
    Run the command line parser
    """
    try:
      opts, args = getopt.getopt(args, "a:c:dfhlr:st:u:v:w",
                                 ["attribute=", "all", "claim-id=", "disclaim", 
                                  "fetch", "help", "help-full", "list", 
                                  "logdir=", "reason=", "shell", "timeout=",
                                  "type=", "user=", "value=", "wait"])
    except getopt.GetoptError, ex:
      self.usage(2, str(ex))
    
    if len(opts) == 0:
      self.usage(2, "One or more options are required")

    options = {'resourcerequirements':{}}
    restype = None
    attribute = None

    try:
      options['user'] = getpass.getuser()
    except Exception:
      pass

    for (opt, arg) in opts:
      if opt in ("-a", "--attribute"):
        if restype == None:
          self.usage(3, "Attribute option must follow type option")
        if not arg in options['resourcerequirements'][restype]:
          options['resourcerequirements'][restype][arg] = []
        attribute = arg
      elif opt == "--all":
        options['all'] = True
      elif opt in ("-c", "--claim-id"):
        try:
          options['claimid'] = int(arg)
        except ValueError:
          self.usage(2, "Claim IDs must be numeric")
      elif opt in ("-d", "--disclaim"):
        options['mode'] = "disclaim"
      elif opt in ("-f", "--fetch"):
        options['mode'] = "fetch"
      elif opt in ("-h", "--help"):
        self.usage(0)
      elif opt == "--help-full":
        self.usage(0, full=True)
      elif opt in ("-l", "--list"):
        options['mode'] = "list"
      elif opt == "--logdir":
        options['logdir'] = arg
      elif opt in ("-r", "--reason"):
        options['reason'] = arg
      elif opt in ("-s", "--shell"):
        options['shell'] = True
      elif opt in ("-t", "--type"):
        if not arg in options['resourcerequirements']:
          options['resourcerequirements'][arg] = {}
        restype = arg
        attribute = None
      elif opt == "--timeout":
        try:
          # Timeout is in minutes but we count in batches of 20 seconds so 
          # multiply by 3
          options['timeout'] = 3 * int(arg)
        except ValueError:
          self.usage(2, "Timeout values must be numeric")
      elif opt in ("-u", "--user"):
        options['user'] = arg
      elif opt in ("-v", "--value"):
        if attribute == None:
          self.usage(3, "Value option must follow attribute option")
        if not arg in options['resourcerequirements'][restype][attribute]:
          options['resourcerequirements'][restype][attribute].append(arg)
      elif opt in ("-w", "--wait"):
        options['wait'] = True

    return self.doClaim(options)

  def setDefaults(self, options):
    """
    Set the default claim options
    """
    self.setDefault(options, 'user', None)
    self.setDefault(options, 'userid', None)
    self.setDefault(options, 'mode', "claim")
    self.setDefault(options, 'wait', False)
    self.setDefault(options, 'timeout', None)
    self.setDefault(options, 'claimid', None)
    self.setDefault(options, 'shell', False)
    self.setDefault(options, 'all', False)
    self.setDefault(options, 'reason', None)
    self.setDefault(options, 'type', None)
    self.setDefault(options, 'attribute', None)
    self.setDefault(options, 'resourcerequirements', {})
    self.setDefault(options, 'noexit', False)
    self.setDefault(options, 'logdir', None)

  def setDefault(self, options, option, value):
    """
    Set a single default value
    """
    if not option in options:
      options[option] = value

  def doClaim(self, options):
    """
    Do the claim setting defaults where missing from the options array
    """
    self.setDefaults(options)

    if options['user'] != None:
      userid = self.ovtDB.getUserByName(options['user'])
      if userid == None:
        self.error("User '%s' does not exist" % (options['user']))
        sys.exit(2)
      options['userid'] = userid
    else:
      self.error("User not specified")
      sys.exit(2)

    if options['mode'] == "claim":
      return self.__doClaimClaim (options)

    elif options['mode'] == "disclaim":
      return self.__doClaimDisclaim (options)

    elif options['mode'] == "list":
      return self.__doClaimList (options)

    elif options['mode'] == "fetch":
      return self.__doClaimFetch (options)

    return True

  def __doClaimFetch(self, options):
    """
    Do an actual fetch attributes
    """
    if options['claimid'] == None and options['reason'] == None:
      self.error("Cannot fetch resources without the claim reason or number")
      sys.exit(2)

    if options['claimid'] != None:
      options['reason'] = None

    claim = self.ovtDB.getUserClaim(options['claimid'], options['userid'],
                                    options['reason'])

    if claim == None:
      if options['claimid'] != None:
        self.error("Claim [%d] does not exist" % options['claimid'])
      else:
        self.error("You have no claims with the reason '%s'"
                   % options['reason'])
      sys.exit(2)

    if claim['grantdate'] == None or claim['returndate'] != None:
      self.error("The claim is not granted or has been returned")
      sys.exit(2)
    
    if len(options['resourcerequirements']) != 1:
      self.error("Please specify (exactly) one type of resource and (exactly) one attribute")
      sys.exit(2)

    restype = options['resourcerequirements'].keys()[0]
    if len(options['resourcerequirements'][restype]) != 1:
      self.error("Please specify (exactly) one type of resource and (exactly) one attribute")
      sys.exit(2)

    attribute = options['resourcerequirements'][restype].keys()[0]

    values = self.ovtDB.getClaimInfo(claim['userclaimid'], type=restype,
                                     attribute=attribute)
    if len(values) == 0:
      self.error("%s attribute not found for %s resource type"
                 % (attribute, restype))
      sys.exit(2)
    elif len(values) == 1:
      print values[0]
    else:
      print (",".join(values))
    sys.exit(0)

  def __doClaimList(self, options):
    """
    Do an actual list
    """
    if options['all']:
      print "List all active claims"
      requests = self.ovtDB.listUserClaims()
    else:
      print "List active claims for %s" % options['user']
      requests = self.ovtDB.listUserClaims(userid=options['userid'])
    if len(requests[0]) == 0:
      if options['all']:
        print "There are no active claim requests"
      else:
        print "You have no active claim requests"
    self.printRequests(requests, options['all'])

  def __doClaimDisclaim(self, options):
    """
    Do an actual disclaim
    """
    if options['claimid'] == None and options['reason'] == None:
      self.error("Disclaiming resources requires a claim ID or a reason")
      sys.exit(3)

    claim = self.ovtDB.getUserClaim(options['claimid'],
                                    userid=options['userid'],
                                    reason=options['reason'])
    if claim == None:
      if options['claimid'] != None:
        self.error("Claim [%d] does not exist" % options['claimid'])
      else:
        self.error("You have no claims with the reason '%s'"
                   % options['reason'])
      sys.exit(4)

    if claim['userid'] != options['userid']:
      self.error("Claim [%d] is not owned by you it is owned by %s"
                 % (claim['userclaimid'], claim['username']))
      sys.exit(4)

    if claim['returndate'] != None:
      self.error("Claim [%d] has already been returned"
                 % (claim['userclaimid']))
      if options['noexit']:
        return False
      sys.exit(4)

    print "Returning resources for claim [%d]" % claim['userclaimid']
    self.ovtDB.releaseUserResources(claim['userclaimid'])
    requests = self.ovtDB.listUserClaims(userclaimid=claim['userclaimid'])
    self.printRequests(requests)
    return True

  def __doClaimCreate(self, options):
    """
    Create a claim or fetch it from the database
    """
    if options['claimid'] == None and \
       len(options['resourcerequirements']) != 0:
      attributevalueids = set()
      for restype in options['resourcerequirements']:
        for attribute in options['resourcerequirements'][restype]:
          for value in options['resourcerequirements'][restype][attribute]:
            attributevalueid = self.ovtDB.getAttributeValueByName(restype,
                                                                  attribute, 
                                                                  value)
            if attributevalueid == None:
              self.error("There is no %s attribute with value %s for the %s type of resource"
                         % (attribute, value, restype))
              sys.exit(4)
            attributevalueids.add(attributevalueid)
      if options['reason'] == None:
        self.error("No reason given for this request")
        sys.exit(5)
      elif not self.ovtDB.checkUniqueClaimReason(options['userid'],
                                                 options['reason']):
        self.error("Reasons for active claims must be unique, please state a different reason")
        sys.exit(5)

      try:
        userclaimid = self.ovtDB.makeUserClaim(options['userid'],
                                               options['reason'],
                                               attributevalueids)
      except UniqueError:
        self.error("Reasons for active claims must be unique, please state a different reason")
        sys.exit(5)

      print "New claim created: [%d]" % userclaimid
    elif options['claimid'] != None or options['reason'] != None:
      claim = self.ovtDB.getUserClaim(options['claimid'], options['userid'],
                                      options['reason'])
      if claim == None:
        if options['claimid'] != None:
          self.error("Claim [%d] does not exist" % options['claimid'])
        else:
          self.error("You do not have a claim with reason '%s'"
                     % options['reason'])
        sys.exit(4)

      if claim['userid'] != options['userid']:
        self.error("Claim [%d] is not owned by you it is owned by %s"
                   % (claim['userclaimid'], claim['username']))
        sys.exit(4)
      userclaimid = claim['userclaimid']
    else:
      self.error("Please specify a reason or claimid to retrieve an existing claim\n" +\
                 "or specify a reason and some requirements to make a new claim")
      sys.exit(4)

    return userclaimid

  def __doClaimInitialise(self, userclaimid, options):
    """
    Initialise all the resources in a claim
    """
    resourceids, historic = self.ovtDB.getUserResources(userclaimid, held=True)
    if len(resourceids) == 0:
      self.error("Internal consistency failure... The claim resulted in no resources.")
      sys.exit(4)

    self.globals = {'resources':{}}
    self.userclaimid = userclaimid
    testrun = DevTestrun(self.globals, 0)
    testrun.log_helper_message = "STATUS"
    for resourceid in resourceids:
      data = self.ovtDB.getUserResource(userclaimid, resourceid)
      resource = None

      try:
        exec("from resources.R%u import *" % (data['typeid']))
        exec("resource = R%u((testrun, {'userclaimid':userclaimid, 'logdir':options['logdir']}, data))"
             % (data['typeid']))
        exec("del(sys.modules['resources.R%u'])" % (data['typeid']))
      except ImportError, e:
        self.error("Failed to import module for %s resource (R%u)"
                   % (data['name'], data['typeid']))
        self.error(e)
        raise ResourceInitFailedException("Import error") 
      except SyntaxError:
        self.error("Syntax error in %s resource module (R%u)\n%s"
                   % (data['name'], data['typeid'],
                      formatExceptionInfo()))
        raise ResourceInitFailedException("Syntax error") 
      except Exception:
        self.error("Unknown exception in %s resource module (R%u)\n%s"
                   % (data['name'], data['typeid'],
                      formatExceptionInfo()))
        raise ResourceInitFailedException("Unknown error") 

      print "Successfully claimed %s" % resource.getName()
      self.globals['resources'][resource.getType()] = resource

    # Crudely sort the resource initialisation to initialise
    # in alphabetic order
    for restype in sorted(self.globals['resources'].keys()):
      try:
        if self.globals['resources'][restype].initialiseChecked():
          # If the resources used are not historic create them so that next
          # time this claim is re-initialised the exact same resource config
          # will be used. This also serves to provide a long term record
          # of the exact resource configuration
          if not historic:
            self.ovtDB.cloneResource(self.globals['resources'][restype].getResourceid(), 
                                     self.globals['resources'][restype].getAttributes(),
                                     userclaimid=userclaimid)
          print "Successfully initialised %s" \
                % (self.globals['resources'][restype].getName())
      except ResourceInitFailedException:
        print "Failed to initialise %s, check log files" \
              % (self.globals['resources'][restype].getName())
        raise
      except Exception:
        print "Exception during initialisation of %s\n%s" \
              % (self.globals['resources'][restype].getName(),
                 formatExceptionInfo())
        raise ResourceInitFailedException("Init exception")
    return True

  def __doClaimClaim(self, options):
    """
    Do an actual claim
    """
    userclaimid = self.__doClaimCreate (options)
    
    waitmessage = True
    try:
      while True:
        success = False
        acquired = False
        try:
          try:
            while not success:
              try:
                self.ovtDB.setAutoCommit(False)
                claim = self.ovtDB.getUserClaim(userclaimid)
                if claim['returndate'] != None:
                  raise ClaimReturnedException("The claim has already been returned (on %s)"
                                               % claim['returndate'])
                if self.ovtDB.acquireUserResources(userclaimid):
                  acquired = True
                self.ovtDB.FORCECOMMIT()
                self.ovtDB.setAutoCommit(True)
                success = True
              except DatabaseRetryException, ex:
                pass
          finally:
            if not success:
              self.ovtDB.FORCEROLLBACK()
              self.ovtDB.setAutoCommit(True)
        except AllocationException, ex:
          self.error(str(ex))
          # Cancel resource request
          self.ovtDB.releaseUserResources(userclaimid)
          self.error("Request %d cancelled" % userclaimid)
          sys.exit(2)
        except AllocationAbortException, ex:
          self.error("### ALERT ### Contact overtest admin, serious internal error")
          self.error(str(ex))
          # Cancel resource request
          self.ovtDB.releaseUserResources(userclaimid)
          self.error("Request %d cancelled" % userclaimid)
          sys.exit(2)
        except ClaimReturnedException, ex:
          self.error(str(ex))
          sys.exit(2)
  
        if acquired:
          return self.__doClaimInitialise(userclaimid, options)
        else:
          # Check to see if any of the resources we are queued on are
          # 'no queue'
          requests = self.ovtDB.listUserClaims(userclaimid=userclaimid)
          resources = requests[0][userclaimid]['resources']
          for resource in resources:
            if resources[resource]['nouserqueue'] and \
               resources[resource]['position'] > 0:
              raise NoQueueException("Claim on %s is not queueable and is in use"
                                     % resource)
        if not acquired and options['timeout'] == None and \
           not options['wait']:
          print "Queued to claim resources. Please wait..."
          requests = self.ovtDB.listUserClaims(userclaimid=userclaimid)
          self.printRequests(requests)
          return False
        if waitmessage:
          print "Waiting for resources. Retrying every 20 seconds"
          if options['timeout'] != None:
            print "Timeout in %d minutes" % int(options['timeout']/3)
          waitmessage = False
        if options['timeout'] != None:
          if options['timeout'] == 0:
            raise TimeoutException("Resource request timed out")
          options['timeout'] -= 1
        # Sleep a bit before trying again
        time.sleep(20)
    except (KeyboardInterrupt):
      print "Releasing resources"
      self.ovtDB.releaseUserResources(userclaimid)
      return False
    except (ResourceInitFailedException,
            TimeoutException, NoQueueException), ex:
      print "Releasing resources"
      self.ovtDB.releaseUserResources(userclaimid)
      print ex
      return False

  def printRequests(self, requests, all = False):
    """
    Print out a requests structure
    """
    currentuser = ""
    indent = 0
    maxlen = 0
    # Extract the real data
    (requests, order) = requests
    for claimid in requests:
      currid = "%d" % claimid
      if len(currid) > maxlen:
        maxlen = len(currid)

    for claimid in order:
      if all and requests[claimid]['details']['username'] != currentuser:
        currentuser = requests[claimid]['details']['username']
        print "Claims for %s" % currentuser
        indent = 2
      claimnumber = ("[%s]" % bold(str(claimid))).ljust(maxlen + 2)
      claimindent = len(("[%s]" % str(claimid)).ljust(maxlen + 2))
      state = None
      if requests[claimid]['details']['returndate'] != None:
        print "%s%s %s" % (" " * indent, claimnumber,
                           bold("returned on %s because '%s'"
                                % (requests[claimid]['details']['returndate'],
                                   requests[claimid]['details']['reason'])))
        state = "returned"
      elif requests[claimid]['details']['grantdate'] != None:
        print "%s%s %s" % (" " * indent, claimnumber,
                           bold(" granted on %s because '%s'"
                                % (requests[claimid]['details']['grantdate'],
                                   requests[claimid]['details']['reason'])))
        state = "holding"
      else:
        print "%s%s %s" % (" " * indent, claimnumber,
                           bold("    made on %s because '%s'"
                                % (requests[claimid]['details']['requestdate'],
                                   requests[claimid]['details']['reason'])))
        state = "requesting"

      resources = requests[claimid]['resources']
      resmaxlen = 0
      for resourcename in resources:
        if len(resourcename) > resmaxlen:
          resmaxlen = len(resourcename)

      for resourcename in resources:
        resource = resources[resourcename]
        resname = ("'%s'" % resourcename).ljust(resmaxlen + 2)
        if state == "requesting":
          if resource['heldbyautomation']:
            print "%s Requesting %s [queue position %d] and held by automation system" \
                  % (" "*(indent+claimindent), resname, resource['position'])
          else:
            if resource['position'] == 0:
              print "%s Requesting %s [READY TO CLAIM]" \
                    % (" "*(indent+claimindent), resname)
            else:
              print "%s Requesting %s [queue position %d]" \
                    % (" "*(indent+claimindent), resname, resource['position'])
        elif state == "holding":
          print "%s Holding %s" % (" " * (indent+claimindent), resname)
        elif state == "returned":
          print "%s Released %s" % (" " * (indent+claimindent), resname)
