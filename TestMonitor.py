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
from Interactive import Interactive
from textwrap import TextWrapper
from TestManager import TestrunFactory
from utils.TerminalUtilities import *
from HostAllocator import HostAllocator
from OvertestExceptions import *
import getpass
import getopt
import sys
import types
import pickle
import os
from LogManager import LogManager
from Config import CONFIG

class TestMonitor(Interactive):
  def __init__(self, _ovtDB):
    Interactive.__init__(self, _ovtDB)
    self.wrapper = TextWrapper(initial_indent="   Description: ", subsequent_indent="                ", expand_tabs=False)
    self.log = LogManager("monitor", True, local=True)
    self.ovtDB.registerLog(self.log)

  def usage(self, exitcode, error = None, full=False):
    """
    Display the usage
    """
    if error != None:
      self.printerror(error)
      print ""
 
    print "Usage:"
    print "TestMonitor [OPTIONS]"
    print "Options:"
    print "--sync                    Push local log files to web server"
    print "-u <user> --user=<user>   Specify user to connect as"
    print "-i <testrunid> --testrunid=<testrunid>"
    print "                          Dump a testrun by number"
    sys.exit(exitcode)

  def printerror(self, error):
    """
    Print an error message
    """
    sys.stderr.write("ERROR: %s\n"%error)
  
  def header(self):
    """
    Print a standard header for this module
    """
    clearscreen()
    print blue("-"*80)
    print blue("|")+ ("Overtest - Test Monitor").center(78)+blue("|")
    print blue("-"*80)
    print blue("|")+ ("Connected as: "+green(self.user)).rjust(78+len(green("")))+blue("|")
    print blue("-"*80)
    self.printMessages()

  def run(self, args):
    """
    Allows a user to investigate their active and historic testrun data
    """
    # Get user from shell login
    self.user = None
    testrunid = None
    try:
      self.user = getpass.getuser()
    except Exception:
      pass

    try:
      opts, args = getopt.getopt(args, "i:u:", ["testrunid=", "user=", "sync"])
    except getopt.GetoptError, e:
      setupScreen()
      self.usage(2, str(e))

    for (o,a) in opts:
      if o in ("-u", "--user"):
        self.user = a
      elif o in ("-i", "--testrunid"):
        testrunid = int(a)
      elif o == "--sync":
        actions = self.ovtDB.searchActions({"secure":True})
        import commands
        import tempfile
        exclude_file = tempfile.NamedTemporaryFile()
        for actioncategoryid in actions[0]:
          for actionid in actions[0][actioncategoryid]['related'][0]:
            versions = self.ovtDB.searchActions({"actionid":actionid})
            for vaid in versions[0][actioncategoryid]['related'][0][actionid]['related'][0]:
              exclude_file.write("*/%s\n"%vaid)
        exclude_file.write("*/*/work\n")
        exclude_file.write("*/*/shared\n")
        exclude_file.flush()
        # Log files need to be world readable, there is nothing secret in them
        result = commands.getstatusoutput("chmod -R a+r %s" % (CONFIG.logdir))
        # Ignore errors - things like swap files when viewing logs can get in the way
        # Log files need to be world readable, there is nothing secret in them
        result = commands.getstatusoutput("find %s -type d -exec chmod a+x {} \;" % (CONFIG.logdir))
        if result[0] != 0:
          print result[1]
        # Push all log files to the server EXCEPT those in actions marked as secure
        result = commands.getstatusoutput("rsync -rztlWvHp --exclude-from=%s %s mfortune@overtest.le.imgtec.org:/home/overtest/root" % (exclude_file.name, CONFIG.logdir))
        exclude_file.close()
        if result[0] != 0:
          print result[1]
        sys.exit(result[0])

    userid = self.ovtDB.getUserByName(self.user)
    if userid == None:
      print "User %s does not exist" % self.user
      return
    self.factory = TestrunFactory(self.user, self.ovtDB)
    if testrunid is not None:
      try:
	(success, testrun) = self.factory.fetchTestrun(testrunid)
      except ImpossibleDependencyException, e:
	print "Inconsistent testrun"
	sys.exit(1)
      self.generateManualTestHarness(testrunid, testrun)
      sys.exit(0)

    setupScreen()

    mainquit = False
    while not mainquit:
      self.header()
      self.wrapper.initial_indent="   Description: "
      self.wrapper.subsequent_indent="                "
      testruns = self.ovtDB.getTestruns(userid,active = True)
      print "Active testruns: "
      print blue("-"*80)
      i = 1
      for testrun in testruns:
        print magenta(str(i))+ ") Created: "+green(testrun['createddate'])+" Status: "+green(testrun['status'])
        print cyan("   %s"%testrun['testrungroupname'])
        if testrun['description'] != None:
          print self.wrapper.fill(green(testrun['description']))
        i+=1
      if len(testruns) == 0:
        print "No testruns available"
      print blue("-"*80)
      choice = raw_input("Select a testrun (h for historic testruns or q for exiting): ")
      if choice != "h":
        if choice != "q":
          try:
            choice = int(choice)
          except ValueError:
            continue
          if choice == 0:
            mainquit = True
          else:
            self.showTestrunDetail(testruns[choice-1]['testrunid'])
        elif choice == "q":
            mainquit = True
      else:
        page = 1
        quit = False
        while not quit:
          self.header()
          self.wrapper.initial_indent="   Description: "
          self.wrapper.subsequent_indent="                "
          print "Historic testruns - Page " + str(page)
          print blue("-"*80)
          testruns = self.ovtDB.getTestruns(userid, active = False, page = page)
          i = 1
          for testrun in testruns:
            print magenta(str(i))+") Created: "+green(testrun['createddate'])+" Status: "+green(testrun['status'])
            print cyan("   %s"%testrun['testrungroupname'])
            if testrun['description'] != None:
              print self.wrapper.fill(green(testrun['description']))
            i+=1
          if len(testruns) == 0:
            print "No testruns available"
          print blue("-"*80)
          print magenta("p")+") Previous page"
          print magenta("n")+") Next page"
          print magenta("a")+") View active testruns"
          print magenta("#")+") Select testrun by number"
          print magenta("0")+") Exit"
          print blue("-"*80)
          choice = raw_input("Select a testrun or an option: ")
          if choice == "p":
            if page != 1:
              page -= 1
          elif choice == "n":
            page += 1
          elif choice == "a":
            quit = True
          elif choice == "#":
            testrunid = raw_input("Enter testrun number: ")
            self.showTestrunDetail(int(testrunid))
          else:
            try:
              choice = int(choice)
            except ValueError:
              continue
            if choice == 0:
              quit = True
              mainquit = True
            else:
              self.showTestrunDetail(testruns[choice-1]['testrunid'])

  def showTestrunDetail(self,testrunid):
    """
    Show full status of the executing testrun and enable 'drill down'
    into results
    """
    self.wrapper.initial_indent="Description: "
    self.wrapper.subsequent_indent="             "
    try:
      (success, testrun) = self.factory.fetchTestrun(testrunid)
    except ImpossibleDependencyException, e:
      self.error = "SEVERE: Testrun is inconsistent"
      return
      
    if not success:
      print testrun
    else:
      details = testrun.getDetails()
      quit = False
      while not quit:
        self.header()
        print "Viewing testrun created: "+green(details['createddate'])+" Status: "+green(details['status'])
        print cyan(details['testrungroupname'])
        if details['description'] != None:
          print self.wrapper.fill(green(details['description']))
        print blue("-"*80)
        testrun.printTests(showids=True)
        if len(details['resultcounts']) != 0:
          i = 0
          for result in details['resultcounts']:
            i+=1
            print yellow(result)+"=>"+green(str(details['resultcounts'][result]))+" ",
            if i == 3:
              print ""
              i = 0
          if i != 0:
            print ""
        print blue("-"*80)
        print "Resources used:"
        for resourcegroup in details['resources']:
          print yellow(resourcegroup)+" => " +green(details['resources'][resourcegroup])
        print blue("-"*80)
        print magenta("1")+") none"
        print magenta("2")+") none"
        print magenta("3")+") List all actions"
        print magenta("4")+") Show full details for an action"
        print magenta("5")+") Generate manual test harness"
        print magenta("0")+") Return to main"
        choice = self.selectItem("Option", range(0,6))
        if choice == 0:
          quit = True
        elif choice == 1:
          None # Not done
        elif choice == 2:
          None # Not done
        elif choice == 3:
          raw_input("Press enter to continue...")
        elif choice == 4:
          pass
        elif choice == 5:
          self.generateManualTestHarness(testrunid, testrun)
        print blue("-"*80)

  def generateManualTestHarness(self, testrunid, testrun):
    """
    Create a manual test harness for the specified testrun
    """
    # Step 1 : Order the actions based on dependencies
    vaidorder = []
    versionedactioniddict = testrun.versionedactioniddict
    searchvaids = versionedactioniddict.keys()
    dbinit = False

    while len(searchvaids) != 0:
      for vaid in searchvaids:
        if len(set(versionedactioniddict[vaid].keys()) - set(vaidorder)) == 0:
          vaidorder.append(vaid)
      for vaid in vaidorder:
        if vaid in searchvaids:
          searchvaids.remove(vaid)

    # Step 2 : Create a harness with the name testrun_<testrunid>.py
    filename = "testrun_%u.py"%testrunid
    fh = open(filename, "w")
    fh.write("#!/usr/bin/python\n")
    fh.write("# Import the version checker to auto-invoke the correct version of python\n")
    fh.write("import VersionCheck\n")
    fh.write("import sys\n")
    fh.write("import os\n")
    fh.write("import atexit\n")
    fh.write("from Config import CONFIG\n")
    fh.write("import getopt\n")
    fh.write("import pickle\n")
    fh.write("from DevelopmentHarness import DevTestrun\n")
    fh.write("\n")
    fh.write("reset = False\n")
    fh.write("keepclaim = False\n")
    fh.write("concurrency = 1\n")
    fh.write("\n")
    fh.write("args = sys.argv[1:]\n")
    fh.write("if len(args) > 0 and args[0].startswith('-'):\n")
    fh.write("  try:\n")
    fh.write("    opts, args = getopt.getopt(sys.argv[1:], 'rj:k', ['reset','jobs=','keepclaim'])\n")
    fh.write("  except getopt.GetoptError, e:\n")
    fh.write("    self.usage(2, str(e))\n")
    fh.write("\n")
    fh.write("  for (o,a) in opts:\n")
    fh.write("    if o in ('-r','--reset'):\n")
    fh.write("      reset = True\n")
    fh.write("    elif o in ('-j','--jobs'):\n")
    fh.write("      concurrency = int(a)\n")
    fh.write("    elif o in ('-k','--keepclaim'):\n")
    fh.write("      keepclaim = True\n")
    fh.write("\n")
    fh.write("# Set the root path for overtest output\n")
    fh.write("if len(args) != 2:\n")
    fh.write("  print \"Usage: %s [--reset] [--keepclaim] <user> <root directory>\\n\" % sys.argv[0]\n")
    fh.write("  sys.exit(1)\n")
    fh.write("CONFIG.logdir = os.path.abspath(args[1])\n")
    fh.write("CONFIG.shareddir = os.path.abspath(args[1])\n")
    fh.write("CONFIG.localdir = os.path.abspath(args[1])\n")
    fh.write("\n")
    fh.write("claimids = {}\n")
    fh.write("\n")
    fh.write("def initDB():\n")
    fh.write("  \"\"\"\n")
    fh.write("  Set up any database related features (once)\n")
    fh.write("  \"\"\"\n")
    fh.write("  if not 'claims' in globals():\n")
    fh.write("    from OvtDB import OvtDB\n")
    fh.write("    from LogManager import LogManager\n")
    fh.write("    try:\n")
    fh.write("      log = LogManager(None, True)\n")
    fh.write("      ovtDB = OvtDB(log)\n")
    fh.write("    except Exception, e:\n")
    fh.write("      print e\n")
    fh.write("      print 'Failed to connect to database'\n")
    fh.write("      sys.exit(1)\n")
    fh.write("    from ClaimManager import ClaimManager\n")
    fh.write("    globals()['claims'] = ClaimManager(ovtDB)\n")
    fh.write("\n")

    fh.write("# Open the global harness config file\n")
    fh.write("try:\n")
    fh.write("  configfile = open(os.path.join(os.path.expanduser('~'),'.overtest','harness.config'), 'r')\n")
    fh.write("  exec(configfile.read())\n")
    fh.write("except OSError:\n")
    fh.write("  localconfig = {}\n")

    fh.write("\n")
    fh.write("try:\n\n")
    fh.write("# Set up the static config information\n")
    fh.write("  myglobals={'config':{}, 'resources':{}, 'versions':{}, 'defaultdeps':{}, 'testsuites':{}, 'user':args[0]}\n")
    fh.write("\n")

    # Step 3 : Create the initial configuration
    fh.write("# Load initial configuration from file\n")
    configcache = {}
    settings = {}
    for vaid in vaidorder:
      config = self.ovtDB.getVersionedActionConfig(vaid)

      if len(config[1]) != 0:
        settings[vaid] = {}

      for group in config[1]:
        grp = config[0][group]['related']

        for conf in grp[1]:
          configoptionid = grp[0][conf]['id']
          configname = grp[0][conf]['data']

          if not configoptionid in configcache:
            configvalue = self.ovtDB.getConfigSetting(testrunid, vaid, configname)
            configcache[configoptionid] = [configvalue]

          settings[vaid][configname] = configcache[configoptionid]

    # Write out the configuration to a file
    testrun_config = open(".testrun_%d_config"%testrunid, "w")
    pickle.dump((0,settings,{}), testrun_config)
    testrun_config.close()
    fh.write("  testrun_config = open('.testrun_%d_config', 'r')\n"%testrunid)
    fh.write("  (runstate,myglobals['config'],claimids) = pickle.load(testrun_config)\n")
    fh.write("  testrun_config.close()\n")
    fh.write("\n")
    fh.write("  def saveConfig():\n")
    fh.write("    \"\"\"\n")
    fh.write("    Saves the current configuration state to a file\n")
    fh.write("    \"\"\"\n")
    fh.write("    testrun_config = open('.testrun_%d_config', 'w')\n"%testrunid)
    fh.write("    pickle.dump((runstate,myglobals['config'],claimids),testrun_config)\n")
    fh.write("    testrun_config.close()\n")
    fh.write("\n")

    # Handle early exits safely
    fh.write("  def disclaimall():\n")
    fh.write("    \"\"\"\n")
    fh.write("    Cleans up all manual claims and returns the resources\n")
    fh.write("    \"\"\"\n")
    fh.write("    for vaid in globals()['claimids']:\n")
    fh.write("      claimopts = {}\n")
    fh.write("      claimopts['mode'] = 'disclaim'\n")
    fh.write("      claimopts['user'] = myglobals['user']\n")
    fh.write("      claimopts['claimid'] = globals()['claimids'][vaid]\n")
    fh.write("      claimopts['noexit'] = True\n")
    fh.write("      if not claims.doClaim(claimopts):\n")
    fh.write("        print 'Failed to return resources for claim [%d]' % globals()['claimids'][vaid]\n")
    fh.write("    globals()['claimids'] = {}\n")
    fh.write("    saveConfig()\n")
    fh.write("\n")
    fh.write("  def check_disclaimall():\n")
    fh.write("    if not keepclaim:\n")
    fh.write("      disclaimall()\n")
    fh.write("\n")
    fh.write("  atexit.register(check_disclaimall)\n")
    fh.write("\n")

    fh.write("  if reset:\n")
    fh.write("    runstate = 0\n")
    fh.write("    initDB()\n")
    fh.write("    disclaimall()\n")
    fh.write("\n")

    # Step 4 : Write all version strings
    fh.write("# Version information\n")
    for vaid in vaidorder:
      version = self.ovtDB.getVersionInfo(vaid)
      (junkactionid, actionname, junktestrunactionid) = self.ovtDB.getInfoForVersionedAction(testrunid, vaid)
      fh.write("  myglobals['versions'][%u] = (\"%s\",%d)\n" % (vaid, version, vaid))
      fh.write("  myglobals['versions']['%s'] = (\"%s\",%d)\n" % (actionname, version, vaid))
    fh.write("\n")

    # Step 5 : Write all version strings
    fh.write("# Dependency information\n")
    defaultdeps = self.ovtDB.getDefaultDependenciesInTestrun(testrunid)
    for consumeraction in defaultdeps:
      fh.write("  myglobals['defaultdeps']['%s'] = []\n" % (consumeraction))
      for produceraction in defaultdeps[consumeraction]:
        fh.write("  myglobals['defaultdeps']['%s'].append('%s')\n" % (consumeraction, produceraction))
    fh.write("\n")
   
    # Step 6 : Create the testrun
    fh.write("# Create a development testrun\n")
    fh.write("  testrun=DevTestrun(myglobals, testrunid = %u)\n"% testrunid)
    fh.write("\n")

    # Step 7 : Create dummy execution host!
    fh.write("# Execution Host information\n")
    hostAllocator = HostAllocator(self.ovtDB)

    try:
      hosts = hostAllocator.findHosts(testrunid)
    except (AllocationException, AllocationAbortException), e:
      fh.write("INVALID INVALID INVALID");
      fh.close()
      self.info = str(e)
      return

    hostid = hosts[0]

    resources = self.ovtDB.getResources(None, hostid)
    resource = resources[0][hostid]
    groupname = resource['related'][0][resource['related'][1][0]]['data']
    attributes = resource['related'][0][resource['related'][1][0]]['related'][0]
    
    fh.write("  data = {}\n")
    fh.write("  data['attributes'] = {}\n")
    for attributeid in attributes:
      attributename = attributes[attributeid]['data']
      fh.write("  data['attributes'][\"%s\"] = []\n" % attributename.replace("\"", "\\\""))
      values = attributes[attributeid]['related'][0]
      for value in values:
        fh.write("  data['attributes'][\"%s\"].append(\"%s\")\n"% (attributename.replace("\"", "\\\""), values[value]['data'].replace("\"", "\\\"")))

    host_requirements = self.ovtDB.getTestrunsToAllocate(testrunid)[testrunid]['attributes']
    fh.write("  data['requested'] = {}\n")
    requests = {}
    for attributevalueid in host_requirements:
      info = self.ovtDB.simple.getAttributeValueById(attributevalueid)
      attributename = self.ovtDB.simple.getAttributeById(info['attributeid'])['attributename']
      attributevalue = info['value']
      if not attributename in requests:
        requests[attributename] = []
      requests[attributename].append(attributevalue)

    for attributename in requests:
      fh.write("  data['requested']['%s'] = []\n" % attributename.replace("'","\\'"))
      for attributevalue in requests[attributename]:
        fh.write("  data['requested']['%s'].append('%s')\n" % (attributename.replace("'","\\'"), attributevalue.replace("'","\\'")))

    fh.write("  data['name'] = 'Local Host'\n")
    fh.write("  data['hostname'] = 'localhost'\n")
    fh.write("  data['resourceid'] = 0\n")
    fh.write("  data['type'] = 'Execution Host'\n")
    fh.write("  data['typeid'] = 1\n")
    fh.write("\n")
    fh.write("# Override using local config\n")
    fh.write("  if 'host' in localconfig:\n")
    fh.write("    for attribute in localconfig['host']:\n")
    fh.write("      if not attribute in data['attributes']:\n")
    fh.write("        data['attributes'][attribute] = []\n")
    fh.write("      data['attributes'][attribute] = localconfig['host'][attribute]\n")


    fh.write("  try:\n")
    fh.write("    from resources.R1 import *\n")
    fh.write("    execution_host = R1((testrun, {'userclaimid':0}, data))\n")
    fh.write("  except Exception, e:\n")
    fh.write("    print e\n")
    fh.write("    print 'Failed to create Execution Host'\n")
    fh.write("    sys.exit(1)\n")
    fh.write("  myglobals['resources']['Execution Host'] = execution_host\n")

    # Step 8 : Write out all the testsuites
    execution_host_requirements = {}
    fh.write("# Define the testsuites\n")
    testsuites = self.ovtDB.getTestsuitesInTestrun(testrunid)
    for testsuiteid in testsuites:
      # Testsuites need to be searchable by controlling action so invert the
      # dictionary
      fh.write("  myglobals['testsuites'][%u] = %u\n"%(testsuites[testsuiteid], testsuiteid))

    # Step 9 : Run the actions and transfer settings
    fh.write("# Run all actions\n")
    fh.write("  runme = False\n")
    fh.write("  if runstate == 0:\n")
    fh.write("    runme = True\n")
    testrunactionid = 0
    for vaid in vaidorder:
      details = self.ovtDB.getInfoForVersionedAction(testrunid, vaid)

      
      fh.write("  if runme:\n")
      # Put a manual claim request together
      requirements = self.ovtDB.getTestrunActionResourceRequirements(details['testrunactionid'])
      request = {}

      # Determine all the resource types
      for resourcetypeid in requirements:
        resourcetypename = self.ovtDB.simple.getResourceTypeById(resourcetypeid)

        # Separate out the execution host requirements as these need to be dealt
        # with specially (user must be informed)
        if resourcetypename == "Execution Host":
          container = execution_host_requirements
        else:
          if not resourcetypename in request:
            request[resourcetypename] = {}
          container = request[resourcetypename]

        for attributevalueid in requirements[resourcetypeid]:
          # find the attribute and value
          info = self.ovtDB.simple.getAttributeValueById(attributevalueid)
          attributename = self.ovtDB.simple.getAttributeById(info['attributeid'])['attributename']
          attributevalue = info['value']
          if not attributename in container:
            container[attributename] = []
          if not attributevalue in container[attributename]:
            container[attributename].append(attributevalue)

      if len(request) > 0:
        # Create a claim for the required resources
        fh.write("  # The resource requirements\n")
        fh.write("    initDB()\n")
        fh.write("    claimopts = {}\n")
        fh.write("    claimopts['resourcerequirements'] = {}\n")
        for resourcetype in request:
          fh.write("    claimopts['resourcerequirements']['%s'] = {}\n" % resourcetype.replace("'","\\'"))
          for attribute in request[resourcetype]:
            fh.write("    claimopts['resourcerequirements']['%s']['%s'] = []\n" % (resourcetype.replace("'","\\'"), attribute.replace("'","\\'")))
            for value in request[resourcetype][attribute]:
              fh.write("    claimopts['resourcerequirements']['%s']['%s'].append('%s')\n" % (resourcetype.replace("'","\\'"), 
                                                                                           attribute.replace("'","\\'"),
                                                                                           value.replace("'","\\'")))
        fh.write("    claimopts['mode'] = 'claim'\n")
        fh.write("    claimopts['wait'] = True\n")
        fh.write("    claimopts['user'] = myglobals['user']\n")
        fh.write("    if %d in claimids:\n"%vaid)
        fh.write("      claimopts['claimid'] = claimids[%d]\n" % (vaid))
        fh.write("    else:\n")
        fh.write("      claimopts['reason'] = 'manual testrun %d [%d]'\n" % (testrunid, vaid))

        fh.write("    if not claims.doClaim(claimopts):\n")
        fh.write("      print \"Failed to claim resources for: %s\"\n"%details['actionname'])
        fh.write("      sys.exit(1)\n")
        fh.write("\n")
        fh.write("    claimids[%d] = claims.userclaimid\n"%vaid)
        fh.write("    saveConfig()\n")
        fh.write("    myglobals['resources'] = claims.globals['resources']\n")
        fh.write("    myglobals['resources']['Execution Host'] = execution_host\n")

      fh.write("  # Import %s\n"%details['actionname'])
      fh.write("    from action.A%u import A%u\n"%(details['actionid'], details['actionid']))
      fh.write("\n")
      fh.write("  # Create an instance of the action\n")
      fh.write("    test = A%u((testrun, %u, %u, %u))\n"%(details['actionid'], vaid, details['testrunactionid'], details['actionid']))
      fh.write("    test.concurrency = concurrency\n")
      fh.write("    if not test.runChecked():\n")
      fh.write("      print \"Failed whilst running: %s\"\n"%details['actionname'])
      fh.write("      sys.exit(1)\n")
      fh.write("    runstate = %d\n"%vaid)
      fh.write("    saveConfig()\n")
      fh.write("  if runstate == %d:\n"%vaid)
      fh.write("    runme = True\n")
      fh.write("\n")

    fh.write("\n")
    fh.write("except KeyboardInterrupt, e:\n")
    fh.write("  print \"Interrupted\"\n")
    fh.close()
    self.info = "Test harness written to: %s"%filename
