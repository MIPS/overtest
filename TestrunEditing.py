import os
import sys
from OvertestExceptions import *
from LogManager import LogManager
import getopt
import signal
import getpass
import time
import types
from Config import CONFIG
import TestPreparation
from DependencyCheck import DependencyCheck
from HostAllocator import HostAllocator

try:
  import yaml
except ImportError:
  supports_yaml = False
else:
  supports_yaml = True

class TestrunOptions(object):
  def __init__(self, operation = None):
    self.tasks = {}
    self.config = {}
    self.resourcerequirements = {}
    self.user = None
    self.description = None
    self.priority = None
    self.starttime = None
    self.concurrency = None
    self.deptestrunid = None
    self.autoarchive = None
    self.usegridengine = None
    self.testrunid = None
    self.testrungroupid = None
    self.groupname = None
    self.template = None
    self.operation = operation
    self.go = False
    self.wait = None

  def parseYamlTree(self, t):
    """
    Parse the configuration information read from a YAML file.

    :param t: The configuration information
    :type t: dictionary
    :return: Extracted information
    :rtype: tuple
    """
    if 'description' in t:
      self.description = t['description']
    if 'group' in t:
      self.groupname = t['group']
    if 'user' in t:
      self.user = t['user']
    if 'start' in t:
      self.starttime = t['start']

    if 'priority' in t:
      priority = str(t['priority'])
      if not priority.isdigit():
        raise OvtError ("/priority must be specified as a numeric value")
      self.priority = priority

    if 'concurrency' in t:
      concurrency = str(t['concurrency'])
      if not concurrency.isdigit() or concurrency < 1:
        raise OvtError ("/concurrency must be specified as a numeric value")
      self.concurrency = concurrency

    if 'deptestrunid' in t:
      deptestrunid = str(t['deptestrunid'])
      if not deptestrunid.isdigit() or deptestrunid < 1:
        raise OvtError ("/deptestrunid must be specified as a numeric value")
      self.deptestrunid = deptestrunid

    if 'autoarchive' in t:
      autoarchive = t['autoarchive']
      if type(autoarchive) != types.BooleanType:
        raise OvtError ("/autoarchive must be specified as either yes or no")
      self.autoarchive = autoarchive

    if 'usegridengine' in t:
      usegridengine = t['usegridengine']
      if type(usegridengine) != types.BooleanType:
        raise OvtError ("/usegridengine must be specified as either yes or no")
        return fail
      if usegridengine:
	self.autoarchive = True
      self.usegridengine = usegridengine

    if 'definition' in t:
      if type(t['definition']) != types.ListType:
        raise OvtError("Definition must contain a list of actioncategory mappings")
      for item in t['definition']:
        if type(item) != types.DictType:
          raise OvtError("Definition must contain a list of actioncategory mappings")
        for category, actions in item.items():
          if not category in self.tasks:
            self.tasks[category] = {}
          for action, version in actions.items():
            self.tasks[category][action] = version

    if 'configuration' in t:
      if type(t['configuration']) != types.ListType:
        raise OvtError("Configuration must contain a list of option mappings")
      for item in t['configuration']:
        if type(item) != types.DictType:
          raise OvtError("Configuration must contain a list of option mappings")
        for group, assignments in item.items():
          if not group in config:
            self.config[group] = {}
          for option, value in assignments.items():
            if value == None:
              value = ''
            self.config[group][option] = value

    if 'resources' in t:
      if type(t['resources']) != types.ListType:
        raise OvtError("Resources must contain a list of resource type mappings")
      for item in t['resources']:
        if type(item) != types.DictType:
          raise OvtError("Resources must contain a list of resource type mappings")
        for resourcetype, specification in item.items():
          if not resourcetype in self.resourcerequirements:
            self.resourcerequirements[resourcetype] = {}
          for attribute, value in specification['require'].items():
            if not attribute in self.resourcerequirements[resourcetype]:
              self.resourcerequirements[resourcetype][attribute] = []
            if not value in self.resourcerequirements[resourcetype][attribute]:
              self.resourcerequirements[resourcetype][attribute].append(value)


class TestrunEditing:
  def __init__(self, ovtDB):
    """
    Submit a result for an action in a testsuite
    """
    self.ovtDB = ovtDB
    self.log = LogManager(None, True)
    self.ovtDB.registerLog(self.log)
    self.debug=False
    self.testPreparation = TestPreparation.TestPreparation(ovtDB)

  def usage(self, exitcode, error = None):
    """
    Display the usage
    """
    if error != None:
      self.error(error)
      print ""
    print "Testrun Editing Usage:"
    print "-h --help"
    print "         Show this help"
    print "Selecting a mode:"
    print "-n --new"
    print "         Create a new testrun, in potentially a new group"
    print "-c --copy"
    print "         Copy an existing testrun or testrun group"
    print "-e --edit"
    print "         Edit an existing testrun or testrun group"
    print "-f --find"
    print "         Find an existing testrun with a specific configuration"
    print "-s --show"
    print "         Show details about a specific testrun"
    print "-d --delete"
    print "         Delete a testrun"
    print ""
    print "Options for all modes:"
    print "-u <user>"
    print ""
    print "Options for copying and editing:"
    print "-i --testrunid <testrunid>"
    print"          The id of the testrun to edit or copy"
    print "-I --testrungroupid <testrungroupid>"
    print "         The id of the testrun group to edit or copy"
    print ""
    print "Options for copying:"
    print "-T --template <group description>"
    print "         Use the specified template to create a new group of testruns"
    print ""
    print "Options for creating, copying or editing testruns"
    print "   --file <yaml filename>"
    print "         Specify a file to read the configuration from"
    print "-d --description <testrun description>"
    print "         Specify the new description of the testrun (not usable for copying"
    print "         groups or templates"
    print "-D --groupname <group description>"
    print "         Specify the group name to use for a new testrun or group"
    print "-s --starttime <start date/time>"
    print "         Specify the earliest start time for a testrun"
    print "-p --priority <priority>"
    print "         Specify the priority for a testrun (1=highest)"
    print "-j --concurrency <concurrency>"
    print "         Specify the number of concurrent tasks that can execute"
    print "   --deptestrunid <testrunid>"
    print "         Specify a testrun that must complete before this one can start"
    print "   --autoarchive [yes|no]"
    print "         Specify whether the testrun should automatically archive itself on"
    print "         completion. Aborted testruns will not archive automatically."
    print "   --usegridengine [yes|no]"
    print "         Specify whether the testrun should run on the grid engine (implies"
    print "         --autoarchive on"
    print "   --go"
    print "         Start newly created testruns."
    print "-w --wait <state>"
    print "         Wait for newly created testruns to finish."
    print "         external - Set the testrun to be external to overtest."
    print "         complete - Wait until the run completes."
    print ""
    print "The following options specify the contents of a testrun. Each group of 3"
    print "options must be used together. e.g. specify a category, then an action then a"
    print "version. If you need another action in the same category then the category does"
    print "not need to be specified twice. Only one version of any action can be included"
    print "in a single testrun. The same pattern applies to configuration and resource"
    print "requirements except multiple values can be specified for resource attributes."
    print ""
    print "-c --category <category name>"
    print "         The name of a category of actions"
    print "-a --action <action name>"
    print "         The name of an action in a category, must follow a category"
    print "-v --version <version name>"
    print "         The version number of an action to include, must follow an action."
    print "         When updating a testrun a new version of an already included action"
    print "         will automatically remove the existing version"
    print ""
    print "-g --group <config group>"
    print "         The name of a group of options"
    print "-o --option <option name>"
    print "         The name of an option in a category, must follow a group"
    print "-v --value <value>"
    print "         The value to set for an option, must follow an option"
    print ""
    print "-t --type <resource type>"
    print "         The name of a type of resource"
    print "-a --attribute <attribute>"
    print "         The name of an attribute of a resource, must follow a type"
    print "-v --value <value>"
    print "         The value to require for a resource attribute, must follow an"
    print "         attribute"
    print ""
    print "Options for finding testruns:"
    print "--testsuite <testsuite name>"
    print "         The only thing that can be found is an external testrun with a"
    print "         specified testsuite and the testsuite identifier for submitting"
    print "         results is returned"
    print ""
    print "--printall"
    print "         All submission ids from matching testruns will be printed"
    sys.exit(exitcode)

  def error(self, error):
    """
    Print an error message
    """
    print "ERROR: %s"%error

  def execute(self, args):
    """
    Create and issue a new testrun
    """
    lastoptiontype=None
    type = None
    attribute = None
    category = None
    action = None
    group = None
    option = None
    testsuite = None
    printall = False
    opts = TestrunOptions()

    if len(args) == 0:
      self.usage(1, "One or more options are required")
      return False

    try:
      getopts, argsdel = getopt.getopt([args[0]], "cdefhsn", ["copy", "delete", "edit", "find", "help", "show", "new"])
    except getopt.GetoptError, e:
      self.usage(2, str(e))

    if len(getopts) == 0:
      self.usage(2, "The editing operation must be specified first")

    for (o,a) in getopts:
      if o in ("-c", "--copy"):
        opts.operation = "copy"
      if o in ("-d", "--delete"):
        opts.operation = "delete"
      elif o in ("-e", "--edit"):
        opts.operation = "edit"
      elif o in ("-f", "--find"):
        opts.operation = "find"
      elif o in ("-s", "--show"):
        opts.operation = "show"
      elif o in ("-h", "--help"):
        self.usage(0)
      elif o in ("-n", "--new"):
        opts.operation = "new"

    args = args[1:]

    try:
      getopts, args = getopt.getopt(args, "a:c:d:D:g:hi:I:j:o:p:s:t:T:u:v:w:", ["action=","attribute=","autoarchive=","category=","concurrency=","deptestrunid=", "description=","group=","groupname=", "help","option=","priority=","starttime=","template=", "testrunid=","testrungroupid", "testsuite=", "type=","usegridengine=","user=","value=","version=","wait=","go","file=","printall"])
    except getopt.GetoptError, e:
      self.usage(2, str(e))

    if len(getopts) == 0:
      self.usage(2, "One or more options are required")

    for (o,a) in getopts:
      if o in ("-a", "--attribute", "--action"):
        if o != "--action" and lastoptiontype == "resource":
          if not a in opts.resourcerequirements[type]:
            opts.resourcerequirements[type][a] = []
          attribute = a
        elif o != "--attribute" and lastoptiontype == "task":
          if not a in opts.tasks[category]:
            opts.tasks[category][a] = None
          action = a
        elif o == "-a":
          self.usage(3, "-a option must follow either type or category option")
        elif o == "--attribute":
          self.usage(3, "attribute option must follow type option")
        else:
          self.usage(3, "action option must follow category option")
      elif o == "--autoarchive":
        if not a in ("yes", "no"):
          self.usage(3, "autoarchive must be set to yes or no")
        opts.autoarchive = (a == "yes")
      elif o in ("-c", "--category"):
        if not a in opts.tasks:
          opts.tasks[a] = {}
        category = a
        action = None
        lastoptiontype = "task"
      elif o in ("-d", "--description"):
        opts.description = a
      elif o in ("-D", "--groupname"):
        opts.groupname = a
      elif o in ("-g", "--group"):
        if not a in opts.config:
          opts.config[a] = {}
        group = a
        option = None
        lastoptiontype = "config"
      elif o in ("-h", "--help"):
        self.usage(0)
      elif o in ("-i", "--testrunid"):
        if not a.isdigit():
          self.usage(3, "Testrun ids must be specified as a numeric value")
        opts.testrunid = a
      elif o in ("-I", "--testrungroupid"):
        if not a.isdigit():
          self.usage(3, "Testrun ids must be specified as a numeric value")
        opts.testrungroupid = a
      elif o in ("-j", "--concurrency"):
        if not a.isdigit() or a < 1:
          self.usage(3, "Concurrency must be specified as a numeric value")
        opts.concurrency = a
      elif o in ("--deptestrunid"):
        if not a.isdigit() or a < 1:
          self.usage(3, "Dependent testrunid must be specified as a numeric value")
        opts.deptestrunid = a
      elif o in ("-o", "--option"):
        if group == None:
          self.usage(3, "Option option must follow group option")
        if not a in opts.config[group]:
          opts.config[group][a] = None
        option = a
      elif o in ("-p", "--priority"):
        if not a.isdigit():
          self.usage(3, "Priority must be specified as a numeric value")
        opts.priority = a
      elif o in ("-s", "--starttime"):
        opts.starttime = a
      elif o in ("-T", "--template"):
        template = a
      elif o == "--testsuite":
        testsuite = a
      elif o == "--printall":
        printall = True
      elif o in ("-t", "--type"):
        lastoptiontype="resource"
        if not a in opts.resourcerequirements:
          opts.resourcerequirements[a] = {}
        type = a
        attribute = None
      elif o == "--usegridengine":
        if not a in ("yes", "no"):
          self.usage(3, "usegridengine must be set to yes or no")
        opts.usegridengine = (a == "yes")
      elif o in ("-u", "--user"):
        opts.user = a
      elif o in ("-v", "--value", "--version"):
        if o != "--version" and lastoptiontype == "resource":
          if attribute == None:
            self.usage(3, "Value option must follow attribute option")
          if not a in opts.resourcerequirements[type][attribute]:
            opts.resourcerequirements[type][attribute].append(a)
        elif o != "--version" and lastoptiontype == "config":
          if option == None:
            self.usage(3, "Value option must follow option option")
          opts.config[group][option] = a
        elif o != "--value" and lastoptiontype == "task":
          if action == None:
            self.usage(3, "Version option must follow action option")
          opts.tasks[category][action] = a
        elif o == "--value":
          self.usage(3, "Value option must follow either option or attribute option")
        elif o == "--version":
          self.usage(3, "Version option must follow action option")
        else:
          self.usage(3, "-v option must follow either option, attribute or action option")
      elif o == "--go":
        opts.go=True
      elif o in ("-w", "--wait"):
        opts.wait=a
      elif o == "--file":
        if supports_yaml:
          try:
            testrundef = yaml.load (open (a, "r"))
          except IOError, e:
            self.error("Unable to load yaml file %s: %s" % (a, str(e)))
            sys.exit(4)

          if testrundef != None:
	    try:
	      opts.parseYamlTree (testrundef)
	    except OvtError, e:
	      print e
              sys.exit(3)
        else:
          self.error ("--file requires YAML support but this is not available")
          print "Please ensure the YAML module can be found in the PYTHONPATH"
          sys.exit (4)
    try:
      result = self.doTestrunEditing(opts)
      if opts.operation == "new":
	print "New testrun created [%d]" % opts.testrunid
	if opts.go:
	  print result
      elif opts.operation == "copy":
	# Copy a testrun or a testrun group
	if opts.testrunid == None:
	  print "New testrun group created [%d]" % opts.testrungroupid
	else:
	  print "New testrun created [%d]" % opts.testrunid
	if opts.go:
	  print result
      elif opts.operation == "find":
	if len(result) == 0:
	  sys.exit(1)
	else:
	  if printall: # print the whole list of submission ids
	    for s in result:
	      print s
	  else: # print only the first submission id
	    print result[0]
	  sys.exit(0)
      elif opts.operation == "show":
	if supports_yaml:
	  print yaml.dump (result,default_flow_style = False, explicit_start = True)
	else:
	  self.error ("--show requires YAML support but this is not available")
	  print "Please ensure the YAML module can be found in the PYTHONPATH"
	  sys.exit (4)

      if (opts.operation == "new" or opts.operation == "copy") \
	 and opts.go == True and opts.wait == "complete":
        try:
          waitexit = False
          while not waitexit:
            status = self.ovtDB.getTestrunRunstatus(testrunid)
            statusid = self.ovtDB.simple.getRunstatusByName(status)
            statusinfo = self.ovtDB.simple.getRunstatusById(statusid)
            waitexit = statusinfo["deleteenabled"]
            ovt_temp = self.ovtDB
            del ovt_temp
            time.sleep(30)
            self.ovtDB.reconnect(quiet=True)
          if status == "COMPLETED":
            print "Testrun [%d] completed" % testrunid
            sys.exit(0)
          else:
            print "Testrun [%d] FAILED in state %s" % (testrunid, status)
            sys.exit(1)
        except KeyboardInterrupt:
          print "Interrupted by user"
          sys.exit(2)
     
    except OvtError, e:
      print e
      sys.exit(2)

  def doTestrunEditing(self, opts):

    if opts.user == None:
      try:
        opts.user = getpass.getuser()
      except Exception:
        None
 
    if opts.user != None:
      userid = self.ovtDB.getUserByName(opts.user)
      if userid == None:
        raise OvtError("User '%s' does not exist" % (opts.user))
    else:
      raise OvtError("User not specified")

    attributevalueids = set()
    for type in opts.resourcerequirements:
      if len(opts.resourcerequirements[type]) == 0:
        raise OvtError("Incomplete request for the '%s' resource type. Please specify at least one attribute" % type);
      for attribute in opts.resourcerequirements[type]:
        if len(opts.resourcerequirements[type][attribute]) == 0:
          raise OvtError("Incomplete request for the '%s' attribute of the '%s' resource type. Please specify at least one value" % (attribute, type))
        for value in opts.resourcerequirements[type][attribute]:
          attributevalueid = self.ovtDB.getAttributeValueByName(type, attribute, str(value))
          if attributevalueid == None:
            raise OvtError("There is no %s attribute with value %s for the %s type of resource" % (attribute, value, type))
          attributevalueids.add(attributevalueid)

    configsettings = {}
    for group in opts.config:
      if len(opts.config[group]) == 0:
        raise OvtError("Incomplete configuration for the '%s' group. Please specify at least one option" % group)
      for option in opts.config[group]:
        if opts.config[group][option] == None:
          raise OvtError("Incomplete configuration for the '%s' option in the '%s' group. Please specify one value" % (option, group))
        configoptionid, configoptionlookupid = self.ovtDB.getNonAutoConfigOptionByName(group, option, opts.config[group][option])
        if configoptionid == False:
          raise OvtError("There is no '%s' option in the '%s' group with a value of '%s'" % (option, group, opts.config[group][option]))

        configsettings[configoptionid] = (opts.config[group][option], configoptionlookupid)

    versionedactionids = set()
    for category in opts.tasks:
      if len(opts.tasks[category]) == 0:
        raise OvtError("Incomplete task specification in the '%s' category. Please specify at least one action" % category)
      for action in opts.tasks[category]:
        if opts.tasks[category][action] == None:
          raise OvtError("Incomplete task specification for the '%s' action in the '%s' category. Please specify one version" % (category, action))
        versionedactionid = self.ovtDB.getVersionedactionByName(category, action, opts.tasks[category][action])
        if versionedactionid == None:
          raise OvtError("There is no '%s' version of the '%s' action in the '%s' category" % (opts.tasks[category][action], action, category))
        versionedactionids.add(versionedactionid)

    if not opts.go and opts.wait != None and opts.wait != "external":
      raise OvtError("Refusing to wait for a test run that won't be started")

    if opts.operation == "new":
      # Create a new testrun
      if opts.template != None or opts.testrunid != None:
        raise OvtError("template and testrunid options are not valid when creating a new testrun")

      if opts.testrungroupid == None and opts.groupname != None:
        opts.testrungroupid = self.ovtDB.findOrCreateGroup(opts.groupname, userid)

      if opts.testrungroupid == None:
        raise OvtError("Unable to create new testrun, no group specified")

      opts.testrunid = self.ovtDB.createTestrun(opts.description, userid, opts.testrungroupid)
      if self.ovtDB.updateTestrun(opts.testrunid, userid, None, opts.priority, opts.concurrency, opts.starttime,
				  opts.deptestrunid, opts.autoarchive, opts.usegridengine):
        self.ovtDB.modifyTestrunTasks(opts.testrunid, versionedactionids)
        self.ovtDB.modifyTestrunConfig(opts.testrunid, configsettings)
        self.ovtDB.modifyTestrunRequirements(opts.testrunid, attributevalueids)
      else:
        raise OvtError("Unexpected failure when modifying newly created testrun")

    elif opts.operation == "copy":
      # Copy a testrun or a testrun group
      if opts.testrunid == None:
        # Copy a group
        if opts.description != None:
          raise OvtError("Description is not permitted when copying a group as it cannot be applied to multiple testruns")

        # Find the right group to copy
        if opts.testrungroupid == None:
          if opts.template != None:
            opts.testrungroupid = self.ovtDB.getTestrungroupByName(opts.template)
          elif opts.groupname != None:
            opts.testrungroupid = self.ovtDB.getTestrungroupByName(opts.groupname, userid)

          if opts.testrungroupid == None:
            raise OvtError("Unable to copy group without template, testrungroupid or groupname")
        elif opts.template != None:
          raise OvtError("Unable to duplicate group when template and testrungroupid are specified")

        opts.testrungroupid = self.ovtDB.duplicateTestrungroup(opts.testrungroupid, opts.groupname, userid)

        self.ovtDB.updateTestrunGroup(opts.testrungroupid, userid, opts.priority,
				      opts.concurrency, opts.starttime, opts.deptestrunid,
				      opts.autoarchive, opts.usegridengine)
        self.ovtDB.modifyTestrunGroupTasks(opts.testrungroupid, versionedactionids)
        self.ovtDB.modifyTestrunGroupConfig(opts.testrungroupid, configsettings)
        self.ovtDB.modifyTestrunGroupRequirements(opts.testrungroupid, attributevalueids)
      else:
        # Copy a testrun
        if opts.template != None:
          raise OvtError("Templates cannot be used when copying testruns")

        # Find or create the group that the testrun will be placed in
        if opts.groupname != None:
          opts.testrungroupid = self.ovtDB.findOrCreateGroup(opts.groupname, userid)

        opts.testrunid = self.ovtDB.duplicateTestrun(opts.testrunid, opts.testrungroupid,
						     opts.description, userid)
        self.ovtDB.updateTestrun(opts.testrunid, userid, description=None, priority=opts.priority,
                                 concurrency=opts.concurrency, starttime=opts.starttime,
				 deptestrunid=opts.deptestrunid, autoarchive=opts.autoarchive,
				 usegridengine=opts.usegridengine)

        self.ovtDB.modifyTestrunTasks(opts.testrunid, versionedactionids)
        self.ovtDB.modifyTestrunConfig(opts.testrunid, configsettings)
        self.ovtDB.modifyTestrunRequirements(opts.testrunid, attributevalueids)
    elif opts.operation == "edit":
      # Edit a testrun or group
      if opts.testrunid == None:
        raise OvtError("Not implemented")

      if not self.ovtDB.checkTestrun(testrunid, userid):
        raise OvtError("You can only edit your own testruns")

      status = self.ovtDB.getTestrunRunstatus(opts.testrunid)

      self.ovtDB.updateTestrun(opts.testrunid, userid, description=opts.description,
			       priority=opts.priority, concurrency=opts.concurrency,
			       starttime=opts.starttime, deptestrunid=opts.deptestrunid,
			       autoarchive=opts.autoarchive, usegridengine=opts.usegridengine)

      self.ovtDB.modifyTestrunTasks(opts.testrunid, versionedactionids)
      self.ovtDB.modifyTestrunConfig(opts.testrunid, configsettings)
      self.ovtDB.modifyTestrunRequirements(opts.testrunid, attributevalueids)

      if status == "EXTERNAL":
        if opts.groupname != None:
          opts.testrungroupid = self.ovtDB.findOrCreateGroup(opts.groupname, userid)

        self.ovtDB.updateTestrun(opts.testrunid, userid, starttime=opts.starttime,
				 testrungroupid=opts.testrungroupid)

    elif opts.operation == "delete":
      raise OvtError("Not implemented")
    elif opts.operation == "find":
      """
      Locate an 'external' testrun with the given specification
      """
      if opts.groupname != None:
        opts.testrungroupid = self.ovtDB.getTestrungroupByName(opts.groupname, userid)
        if opts.testrungroupid == None:
          raise OvtError("Group not found")

      if opts.testsuite == None:
        raise OvtError("Need a testsuite")
        
      submissionids = self.ovtDB.findTestruns(opts.testsuite, opts.description,
					      opts.testrungroupid, userid,
					      versionedactionids, configsettings,
					      attributevalueids)

      return submissionids
         
    elif opts.operation == "show":
      """
      Describe the testrun as YAML
      """
      if opts.testrunid == None:
        raise OvtError("Testrun not defined")

      details = self.ovtDB.getTestrunDetails(opts.testrunid, sconv=str)

      yaml_dump = {}
      yaml_dump['group'] = details['testrungroupname']
      yaml_dump['description'] = details['description']
      yaml_dump['definition'] = details['definition']
      yaml_dump['requirements'] = details['requirements']
      yaml_dump['configuration'] = details['configuration']

      return yaml_dump
    if opts.operation == "new" or opts.operation == "copy":
      if opts.go == True:
	# Prevent concurrent updates
	if opts.wait != "external" and not self.ovtDB.setTestrunRunstatus(opts.testrunid, "MANUALCHECK"):
	  raise OvtError("Unable to enter manual dependency check phase")
        depcheck = DependencyCheck (self.ovtDB, log=False)
        if not depcheck.checkTestrun (opts.testrunid, self.notify):
	  self.ovtDB.setTestrunRunstatus(opts.testrunid, "CHECKFAILED")
          raise OvtError("Testrun failed dependency checking")
	trinfo = self.ovtDB.simple.getTestrunById(opts.testrunid)

        if opts.wait == "external":
          # Now the testrun needs dependency checking
          # DO NOT ALLOCATE HOSTS
          # Do process/sanitize the config
          # Do mark all tasks as complete and archived
          if not self.ovtDB.updateTestrunStatus(opts.testrunid, "external"):
            raise OvtError("Unable to set testrun to external state")
	elif trinfo['usegridengine']:
	  self.ovtDB.setTestrunRunstatus(opts.testrunid, "CHECKEDGRID")
          return "Testrun [%d] started" % opts.testrunid
	  allocator = HostAllocator(self.ovtDB, self.log)
	  allocator.allocateOneTestrun(opts.testrunid)
	  from imgedaflow import gridinterface
	  cmd = " ".join([CONFIG.python,
			  os.path.join(sys.path[0], "overtest.py"),
			  "-g",
			  "-j", str(trinfo['concurrency']),
			  "-i", str(opts.testrunid)])
	  postcmd = os.path.join(sys.path[0], "addons", "hhuge", "cleanjob.sh")
	  options = {'action'      : 'submit',
		     '--cmd'       : cmd,
		     '--post'      : postcmd,
		     '--batch'     : True, 
		     '--stdouterr' : "/user/mpf/ddddd",
		     '--resources' : 'hdd=ssd,os=rhel6',
		     '--jobname'	 : "ot_%d" % opts.testrunid}
	  if trinfo['concurrency'] > 1:
	    options['--cpucores'] = str(trinfo['concurrency'])
	  ga = gridinterface.GridAccess(**options)
          return_code, job_id = ga.run()
          self.ovtDB.registerGridJob(opts.testrunid, job_id)
          return "Testrun [%d] started as job %s" % (opts.testrunid, job_id)
        else:
          self.ovtDB.setTestrunRunstatus(opts.testrunid, "CHECKED")
          return "Testrun [%d] started" % opts.testrunid

    return True

  def notify(self, message):
    """
    A simple message printer
    """
    print message
