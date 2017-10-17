import sys
import os
from Interactive import Interactive
from utils.TerminalUtilities import *
from OvertestExceptions import *
import getopt

class TestPreparation(Interactive):
  ovtDB = None
  def __init__(self, _ovtDB):
    Interactive.__init__(self, _ovtDB)
    self.config['actions']['addextra'] = self.addActionExtra
    self.config['configoptions']['addextra'] = self.addConfigOptionExtra
    self.config['configoptiongroups']['addextra'] = self.addConfigOptionGroupExtra
    self.showUnavailable = False

  def header(self, title = None):
    """
    Print a standard header for this module
    """
    clearscreen()
    print blue("-"*80)
    print blue("|")+ ("Overtest - Test Preparation").center(78)+blue("|")
    if title != None:
      print blue("|")+ term.BOLD+title.center(78)+term.NORMAL+blue("|")
    print blue("-"*80)
    self.printMessages()

  def usage(self, error = None):
    """
    Display the usage information
    """
    if error != None:
      self.showError(error)

    print "-c --category <category name>"
    print "-a --action <action name>"
    print "-v --version <version name>"
    print ""

  def showError(self, error):
    """
    Print an error
    """
    print "ERROR: %s"%error

  def run(self, args):
    if len(args) == 0:
      setupScreen()
      return self.runInteractive()

    try:
      opts, args = getopt.getopt(args, "a:hc:v:", ["action=","category=","help","version="])
    except getopt.GetoptError, e:
      self.usage(2, str(e))

    if len(opts) == 0:
      self.usage(2, "One or more options are required")

    tasks = {}
    for (o,a) in opts:
      if o in ("-a", "--action"):
        if category == None:
          self.showError("Category required before action option")
          sys.exit(2)
        if not a in tasks[category]:
          tasks[category][a] = None
        action = a
      elif o in ("-c", "--category"):
        if not a in tasks:
          tasks[a] = {}
        category = a
        action = None
      elif o in ("-h", "--help"):
        self.usage()
        sys.exit(1)
      elif o in ("-v", "--version"):
        if action == None:
          self.showError("Action required before version option")
          sys.exit(2)
        tasks[category][action] = a
    
    # Now find the action/version
    versionedactionids = set()
    for category in tasks:
      if len(tasks[category]) == 0:
        self.showError("Incomplete task specification in the '%s' category. Please specify one action" % category)
        sys.exit(4)
      for action in tasks[category]:
        if tasks[category][action] == None:
          self.showError("Incomplete task specification for the '%s' action in the '%s' category. Please specify one version" % (category, action))
          sys.exit(4)
        versionedactionid = self.ovtDB.getVersionedactionByName(category, action, tasks[category][action])
        if versionedactionid == None:
          print "Creating '%s' version of the '%s' action in the '%s' category" % (tasks[category][action], action, category)
          (success, data) = self.createNewVersion(category,action,tasks[category][action])
          if success:
            print "New version: %d"%data
          else:
            self.showError ("Failed to create new version because: %s" % data)
            sys.exit(4)
        else:
          print "Version already exists"

  def createNewVersion(self, category, action, version):
    """
    Create a new version with the specified details
    1) Check that the action exists in the category specified
    2) begin a transaction and take the version lock
    3a) Check that the new version does not already exist
    3b) Find the closest matching existing version
    4) Extract all information on the version
    5) Create the new version
    6) Add all the dependencies, config and requirements
    7) commit
    """
    origactionid = self.ovtDB.getActionByName(category, action)

    # 1) Check that the action exists in the category specified
    if origactionid == None:
      return (False, "Failed to find action")

    # 2) begin a transaction and take the version lock
    success = False
    locked = False
    try:
      while not success:
        try:
          self.ovtDB.setAutoCommit (False)
          locked = True
          self.ovtDB.LOCKACTION (origactionid) 

          # 3a) First ensure the current version does not exist
          versionedactionid = self.ovtDB.getVersionedactionByName(category, action, version)
          if versionedactionid != None:
            return (True, versionedactionid)

          # 3b) Find the closest matching existing version
          versionedactionid = None
          oldversion = version
          while versionedactionid == None:
            # Try matching up to the last '.'
            index = oldversion.rfind(".")
            if index != -1:
              oldversion = oldversion[:index]
            else:
              return (False, "Unable to find version family")

            versionedactionid = self.ovtDB.getMaxVersionedactionFuzzy(origactionid, oldversion)

          # 4) Extract all information on the version
          producers = self.ovtDB.getVersionedActionDependencies (versionedactionid, "Producer")
          consumers = self.ovtDB.getVersionedActionDependencies (versionedactionid, "Consumer")
          configuration = self.ovtDB.getVersionedActionConfig (versionedactionid)
          resourcerequirements = self.ovtDB.getResourceRequirements (versionedactionid)

          # 5) Create the new version
          values = {}
          values['name'] = version
          values['actionid'] = origactionid
          values['lifecyclestateid'] = self.ovtDB.simple.getLifeCycleStateByName("OK")
          newversionedactionid = self.ovtDB.addVersionedAction(values)

          # 6) Add all the dependencies, config and requirements
          # 6a) Create the producer dependencies
          for groupid in producers[1]:
            categories = producers[0][groupid]['related']
            for categoryid in categories[1]:
              actions = categories[0][categoryid]['related']
              for actionid in actions[1]:
                dependencies = actions[0][actionid]['related']
                for dependencyid in dependencies[1]:
                  dependency = dependencies[0][dependencyid]
                  dependencygroupid = None
                  if groupid != -1:
                    dependencygroupid = groupid
                  values = {"dependencygroupid":dependencygroupid,
                            "versiononly":dependency['versiononly'],
                            "hostmatch":dependency['hostmatch'],
                            "defaultdep":dependency['defaultdep']}
                  (success, data) = self.ovtDB.createDependency (consumer=newversionedactionid, producer=dependency['versionedactionid'], values = values)
                  if not success:
                    return (False, data)

          # 6b) Create the consumer dependencies
          for groupid in consumers[1]:
            categories = consumers[0][groupid]['related']
            for categoryid in categories[1]:
              actions = categories[0][categoryid]['related']
              for actionid in actions[1]:
                dependencies = actions[0][actionid]['related']
                for dependencyid in dependencies[1]:
                  dependency = dependencies[0][dependencyid]
                  dependencygroupid = None
                  if groupid != -1:
                    dependencygroupid = groupid
                  values = {"dependencygroupid":dependencygroupid,
                            "versiononly":dependency['versiononly'],
                            "hostmatch":dependency['hostmatch'],
                            "defaultdep":dependency['defaultdep']}
                  (success, data) = self.ovtDB.createDependency (producer=newversionedactionid, consumer=dependency['versionedactionid'], values = values)
                  if not success:
                    return (False, data)

          # 6c) Create the config option links
          for groupid in configuration[0]:
            for configoptionid in configuration[0][groupid]['related'][0]:
              result = self.ovtDB.createConfigOptionLink(newversionedactionid, configoptionid)
              if not result:
                return (False, "Failed to link to config option %d"%configoptionid)
              if configuration[0][groupid]['related'][0][configoptionid]['islookup']:
                option = configuration[0][groupid]['related'][0][configoptionid]
                # And attach the config option lookups
                for configoptionlookupid in option['related'][0]:
                  result = self.ovtDB.createConfigOptionLookupLink(newversionedactionid, configoptionlookupid)
                  if not result:
                    return (False, "Failed to link to config option lookup %d"%configoptionlookupid)

          # 6d) Create the requirements
          for typeid in resourcerequirements[0]:
            for attributeid in resourcerequirements[0][typeid]['related'][0]:
              for attributevalueid in resourcerequirements[0][typeid]['related'][0][attributeid]['related'][0]:
                result = self.ovtDB.createResourceRequirement(newversionedactionid, attributevalueid)
                if not result:
                  return (False, "Failed to require resource attribute %d"%attributevalueid)

          # 7) commit
          self.ovtDB.FORCECOMMIT ()
          success = True
          self.ovtDB.setAutoCommit (True)
        except DatabaseRetryException, e:
          locked = False
    finally:
      self.ovtDB.FORCEROLLBACK ()
      self.ovtDB.setAutoCommit (True)
      self.ovtDB.UNLOCKACTION (origactionid) 
    return (True, newversionedactionid)

  def runInteractive(self):
    exit = False
    try:
      while not exit:
        self.header()
        print "Options:"
        print magenta("1")+") List actions"
        print magenta("2")+") Add action"
        print magenta("3")+") Edit action"
        if self.showUnavailable:
          print magenta("4")+") Turn off 'Show Unavailable items'"
        else:
          print magenta("4")+") Turn on 'Show Unavailable items'"
        print magenta("0")+") Exit"
        choice = self.selectItem("Option", range(0,5))
        if choice == 0:
          exit = True
        elif choice == 1:
          self.findActions()
          self.pause()
        elif choice == 2:
          self.ovtDB.setAutoCommit(False)
          try:
            success = False
            actionid = self.addItem("actions")
            success = True
          finally:
            if success:
              self.ovtDB.FORCECOMMIT()
            else:
              self.ovtDB.FORCEROLLBACK()
            self.ovtDB.setAutoCommit(True)
  
          if actionid == None:
            self.error = "Failed to add action, perhaps it already exists?"
          else:
            overtest_dir = os.path.dirname(sys.argv[0])
            template_fh = None
            module_fh = None
            try:
              template_fh = open(os.path.join(overtest_dir,"action","template.py"), "r")
              template = template_fh.read()
              template_fh.close()
              template_fh = None
              template = template.replace("%actionid%", str(actionid))
              template = template.replace("%actionname%", self.ovtDB.getActionName(actionid))
              module_fh = open(os.path.join(overtest_dir,"action", "A%u.py" % actionid), "w")
              module_fh.write(template)
              module_fh.close()
              module_fh = None
              self.info = "Template has been created in action/A%u.py" % actionid
            except:
              self.error = "Template creation failed"
              if template_fh != None:
                template_fh.close()
              if module_fh != None:
                module_fh.close()
        elif choice == 3:
          self.editAction()
        elif choice == 4:
          self.showUnavailable = not self.showUnavailable
    except (EOFError, KeyboardInterrupt):
      print ""

  def findActions(self):
    try:
      self.config['actioncategories']['showids'] = ["Action Category"]
      categories = self.viewItems('actioncategories', True)
      actioncategoryid = self.selectItem("Category", categories[0])
      if actioncategoryid == 0:
        return

      #searchterm = raw_input("Search term '%' as wildcard: ")
      searchterm = ""
      if searchterm == "":
        searchterm="%"
      more = True
      pagecount = 0
      itemsperpage = 30
      while more:
        search = {"actioncategoryid":actioncategoryid,\
                  "searchterm":searchterm,\
                  "offset":pagecount*itemsperpage,\
                  "limit":itemsperpage}
        (actions, ids) = self.ovtDB.searchActions(search, showunavailable = self.showUnavailable)
        if len(actions) == 0:
          self.error += "No actions found"
          break
        self.config['actions']['showids'] = ["Action"]
        self.viewItems('actions', False, (actions,ids))
        if len(actions) < 1 or len(actions[ids[0]]['related'][0]) < 30:
          break
        askmore = raw_input("More (y/n): ")
        more = False
        if self.checkForYes(askmore):
          more = True
        pagecount += 1
    except (ValueError):
      self.error += "Input error"

  def addActionExtra(self, values):
    self.config['actioncategories']['showids'] = ["Action Category"]
    categories = self.viewItems('actioncategories', True)
    actioncategoryid = self.selectItem("Category", categories[0])
    if actioncategoryid == 0:
      return False
    else:
      values['actioncategoryid'] = actioncategoryid
    yn = raw_input("Is this a testsuite? y/[n] ")
    if self.checkForYes(yn):
      values['istestsuite'] = True
    else:
      values['istestsuite'] = False
    return True

  def editAction(self):
    exit = False
    try:
      self.findActions()
      actionid = int(raw_input("Select Action: "))
    except (ValueError):
      self.error += "Not a number"
      return
    try:
      while not exit:
        self.header("Edit Action")
        search = {"actionid":actionid}
        (actions, ids) = self.ovtDB.searchActions(search, showunavailable=self.showUnavailable)
        if len(actions) != 1:
          self.error += "Action not found"
          return
        self.config['actions']['showids'] = ["Versioned Action"]
        self.printItem("actions", actions[ids[0]])
        print "\n"+magenta("1")+") Edit Action Name"
        print magenta("2")+") Change Category"
        print magenta("3")+") Add Version"
        print magenta("4")+") Edit Version"
        print magenta("5")+") Edit Module Code"
        print magenta("0")+") Exit"
        try:
          choice = self.selectItem("Option", range(0,6))
  
          if choice == 0:
            exit = True
          elif choice == 1:
            newname = raw_input("New name: ")
            if newname != "":
              self.ovtDB.simple.setActionName(actionid, newname)
          elif choice == 2:
            self.config['actioncategories']['showids'] = ["Action Category"]
            categories = self.viewItems('actioncategories', True)
            actioncategoryid = self.selectItem("New Category", categories[0])
            if actioncategoryid != 0:
              self.ovtDB.simple.setActionCategory(actionid, actioncategoryid)
          elif choice == 3:
            self.ovtDB.setAutoCommit(False)
            try:
              self.createVersion(actionid)
              self.ovtDB.setAutoCommit(True)
              self.ovtDB.FORCECOMMIT()
            except KeyboardInterrupt:
              self.error += "New version aborted. Entire update discarded!"
              self.ovtDB.FORCEROLLBACK()
              self.ovtDB.setAutoCommit(True)
          elif choice == 4:
            self.editVersion(actionid)
          elif choice == 5:
            editor = "vim"
            if 'EDITOR' in os.environ:
              editor = os.environ['EDITOR']
            os.system("%s %s" % (editor, os.path.join(os.path.dirname(sys.argv[0]), "action", "A%u.py"%actionid)))
          (actions, ids) =  self.ovtDB.searchActions(search)
        except (ValueError):
          self.error += "Invalid selection"
          continue
    except (EOFError, KeyboardInterrupt):
      print ""

  def editVersion(self, actionid):
    exit = False
    try:
      versionedactionid = int(raw_input("Select Version: "))
    except (ValueError):
      self.error += "Not a number"
      return
    name = self.ovtDB.getVersionedActionName(versionedactionid, actionid=actionid)
    if name == False:
      self.error += "Version not found"
      return
    try:
      while not exit:
        self.header("Edit Version")
        print name
        print "\n"+magenta("1")+") View producers"
        print magenta("2")+") View consumers"
        print magenta("3")+") Create dependency"
        print magenta("4")+") Edit config"
        print magenta("5")+") Edit resource requirements"
        print magenta("6")+") Remove Dependency"
        print magenta("7")+") Toggle Default Dependency"
        print magenta("8")+") Change life cycle state"
        print magenta("9")+") Change name"
        print magenta("0")+") Exit"
        try:
          choice = self.selectItem("Option", range(0,10))
  
          if choice == 0:
            exit = True
          elif choice == 1:
            vadeps = self.ovtDB.getVersionedActionDependencies(versionedactionid, "Producer", showunavailable=self.showUnavailable)
            self.config['dependencies']['showids'] = ["Dependency"]
            self.config['dependencies']['name'] = "Producer"
            self.viewItems("dependencies", False, vadeps)
            self.pause()
          elif choice == 2:
            vadeps = self.ovtDB.getVersionedActionDependencies(versionedactionid, "Consumer", showunavailable=self.showUnavailable)
            self.config['dependencies']['showids'] = []
            self.config['dependencies']['name'] = "Consumer"
            self.viewItems("dependencies", False, vadeps)
            self.pause()
          elif choice == 3:
            self.ovtDB.setAutoCommit(False)
            try:
              self.createDependency(versionedactionid)
              self.ovtDB.setAutoCommit(True)
              self.ovtDB.FORCECOMMIT()
            except KeyboardInterrupt:
              self.error += "Create dependency aborted. Update discarded!"
              self.ovtDB.FORCEROLLBACK()
              self.ovtDB.setAutoCommit(True)
          elif choice == 4:
            self.editConfig(versionedactionid, actionid)
          elif choice == 5:
            self.editResourceRequirements(versionedactionid)
          elif choice == 6:
            vadeps = self.ovtDB.getVersionedActionDependencies(versionedactionid, "Producer", showunavailable=self.showUnavailable)
            self.config['dependencies']['showids'] = ["Dependency"]
            self.config['dependencies']['name'] = "Producer"
            self.viewItems("dependencies", False, vadeps)
  
            dependencyids = []
            for groupid in vadeps[0]:
              group = vadeps[0][groupid]
              for categoryid in group['related'][0]:
                category = group['related'][0][categoryid]
                for actionid in category['related'][0]:
                  action = category['related'][0][actionid]
                  for dependencyid in action['related'][0]:
                    dependencyids.append(dependencyid)
            dependencyid = self.selectItem("Dependency", dependencyids)
            
            if dependencyid == 0:
              continue
  
            if not self.ovtDB.removeDependency(dependencyid):
              self.error="Failed to remove dependency. %s is present in a testrun"%name
          elif choice == 7:
            # Toggle default dependency
            vadeps = self.ovtDB.getVersionedActionDependencies(versionedactionid, "Producer", showunavailable=self.showUnavailable)
            self.config['dependencies']['showids'] = ["Dependency"]
            self.config['dependencies']['name'] = "Producer"
            self.viewItems("dependencies", False, vadeps)
  
            dependencyids = []
            for groupid in vadeps[0]:
              group = vadeps[0][groupid]
              for categoryid in group['related'][0]:
                category = group['related'][0][categoryid]
                for actionid in category['related'][0]:
                  action = category['related'][0][actionid]
                  for dependencyid in action['related'][0]:
                    dependencyids.append(dependencyid)
            dependencyid = self.selectItem("Dependency", dependencyids)
            
            if dependencyid == 0:
              continue
  
            if not self.ovtDB.toggleDefaultDependency(dependencyid):
              self.error="Failed to set default dependency. A conflicting default exists"
          elif choice == 8:
            new_state = self.selectItem("State", range(1,5))
            self.ovtDB.simple.setVersionedActionLifeCycleState (versionedactionid, new_state)
          elif choice == 9:
            newname = raw_input("New name: ")
            if newname != "":
              self.ovtDB.simple.setVersionedActionName(versionedactionid, newname)
              name = self.ovtDB.getVersionedActionName(versionedactionid, actionid=actionid)
        except (ValueError):
          self.error += "Invalid selection"
          continue
    except (EOFError, KeyboardInterrupt):
      print ""

  def selectResourceRequirement(self):
    """
    Select a resource requirement (an attributevalueid)
    """
    requirements = self.ovtDB.getAttributeValues()
    ids = {}
    for resourcetypeid in requirements[0]:
      for attributeid in requirements[0][resourcetypeid]['related'][0]:
        ids[attributeid] = requirements[0][resourcetypeid]['related'][0][attributeid].copy()
        del requirements[0][resourcetypeid]['related'][0][attributeid]['related']
    self.config['attributes']['showids'] = ["Attribute"]
    self.viewItems("attributes", False, requirements)
    attributeid = self.selectItem("Attribute", ids)
    if attributeid == 0:
      return 0
    ids2 = []
    for attributevalueid in ids[attributeid]['related'][0]:
      ids2.append(attributevalueid)
    print "Select a value from the %s attribute" % ids[attributeid]['data']
    self.config['attributevalues']['showids'] = ["Attribute Value"]
    self.viewItems("attributevalues", False, ids[attributeid]['related'])
    attributevalueid = self.selectItem("Requirement", ids2)
    return attributevalueid

  def editResourceRequirements(self, versionedactionid):
    """
    Allows specification of resource requirements by attaching attribute
    values to a versionedaction.
    """
    exit = False
    try:
      while not exit:
        print " Edit Resource Requirements ".center(80, "-")
        print "Editing resource requirements for:"
        print self.ovtDB.getVersionedActionName(versionedactionid)
        requirements = self.ovtDB.getResourceRequirements(versionedactionid)
        attvals = []
        for resourcetypeid in requirements[0]:
          for attributeid in requirements[0][resourcetypeid]['related'][0]:
            for attributevalueid in requirements[0][resourcetypeid]['related'][0][attributeid]['related'][0]:
              attvals.append(attributevalueid)
        self.config['attributevalues']['showids'] = ['Attribute Value']
        self.viewItems("attributevalues", False, requirements)
        print "\n"+magenta("1")+") Add Requirement"
        print magenta("2")+") Remove Requirement"
        print magenta("0")+") Exit"
        try:
          choice = self.selectItem("Option", range(0,3))
  
          if choice == 0:
            exit = True
          elif choice == 1:
            attributevalueid = self.selectResourceRequirement ()
            if attributevalueid != 0:
              self.ovtDB.createResourceRequirement(versionedactionid, attributevalueid)
          elif choice == 2:
            attributevalueid = self.selectItem("Requirement", attvals)
            if attributevalueid != 0:
              self.ovtDB.removeResourceRequirement(versionedactionid, attributevalueid)
  
        except (ValueError):
          self.error += "Invalid selection"
          continue
    except (EOFError, KeyboardInterrupt):
      print ""

  def editConfig(self, versionedactionid, actionid):
    """
    Each versionedaction can be associated with multiple configuration options
    some of these are free text, integer or boolean, and some are lookups.
    A config option can be shared amoungst versionedactions based on the same
    action, or even across multiple actions. Some config options are
    assigned automatically, at test creation or runtime.
    """
    exit = False
    try:
      while not exit:
        print " Edit Config ".center(80, "-")
        print "Editing config for:"
        print self.ovtDB.getVersionedActionName(versionedactionid)
        print "\n"+magenta("1")+") View config"
        print magenta("2")+") Add new option"
        print magenta("3")+") Link to an existing option"
        print magenta("4")+") Un-link an option"
        print magenta("5")+") Link to an existing lookup value"
        print magenta("6")+") Un-link a lookup value"
        print magenta("7")+") Modify a 'lookup' option"
        print magenta("0")+") Exit"
        try:
          choice = self.selectItem("Option", range(0,8))
  
          if choice == 0:
            exit = True
          elif choice == 1:
            config = self.ovtDB.getVersionedActionConfig(versionedactionid)
            self.config['configoptions']['showids'] = []
            self.viewItems("configoptions", False, config)
          elif choice == 2:
            try:
              self.config['configoptions']['showids'] = []
              self.ovtDB.setAutoCommit(False)
              configoptionid = self.addItem("configoptions")
              if configoptionid != None:
                result = self.ovtDB.createConfigOptionLink(versionedactionid, configoptionid)
                if not result:
                  raise KeyboardInterrupt
                else:
                  tempconfig = self.ovtDB.searchConfigOptions(configoptionid=configoptionid)
                  opt = tempconfig[0][tempconfig[1][0]]['related'][0][configoptionid]
                  if opt['islookup']:
                    for configoptionlookupid in opt['related'][0]:
                      result = self.ovtDB.createConfigOptionLookupLink(versionedactionid, configoptionlookupid)
                      if not result:
                        raise KeyboardInterrupt
              else:
                self.error += "Duplicate option specified"
                raise KeyboardInterrupt
              self.ovtDB.setAutoCommit(True)
              self.ovtDB.FORCECOMMIT()
            except KeyboardInterrupt:
              self.error += "New config option aborted. Entire update discarded!"
              self.ovtDB.FORCEROLLBACK()
              self.ovtDB.setAutoCommit(True)
          elif choice == 3:
            self.linkExistingOption(versionedactionid, actionid)
          elif choice == 4:
            self.unlinkOption(versionedactionid)
          elif choice == 5:
            self.linkExistingOptionLookup(versionedactionid)
          elif choice == 6:
            self.unlinkOptionLookup(versionedactionid)
          elif choice == 7:
            self.modifyOption(versionedactionid)
        except (ValueError):
          self.error += "Invalid selection"
          continue
    except (EOFError, KeyboardInterrupt):
      print ""

  def unlinkOption(self, versionedactionid):
    """
    Un-link an option from the specified versioned action.
    Remove the option if this is the last reference
    """
    print " Un-Link Config Option ".center(80, "-")
    print "Removing option from:"
    print self.ovtDB.getVersionedActionName(versionedactionid)
    config = self.ovtDB.getVersionedActionConfig(versionedactionid)
    self.config['configoptions']['showids'] = ["Config Option"]
    self.viewItems("configoptions", False, config)
    print "Removing the last reference to an option will also delete the option"
    configoptionids = []
    for groupid in config[0]:
      for configoptionid in config[0][groupid]['related'][0]:
        configoptionids.append(configoptionid)
    configoptionid = self.selectItem("Config Option", configoptionids)
    if configoptionid != 0:
      self.ovtDB.unlinkAndMaybeRemoveOption(versionedactionid, configoptionid)

  def unlinkOptionLookup(self, versionedactionid):
    """
    Un-link an option lookup from the specified versioned action.
    """
    print " Un-Link Config Option Lookup ".center(80, "-")
    print "Removing option lookup from:"
    print self.ovtDB.getVersionedActionName(versionedactionid)
    config = self.ovtDB.getVersionedActionConfig(versionedactionid)
    self.config['configoptions']['showids'] = ["Config Option Lookup"]
    self.viewItems("configoptions", False, config)
    configoptionlookupids = []
    for groupid in config[0]:
      for configoptionid in config[0][groupid]['related'][0]:
        copt = config[0][groupid]['related'][0][configoptionid]
        if 'related' in copt:
          for configoptionlookupid in copt['related'][0]:
            configoptionlookupids.append(configoptionlookupid)
    configoptionlookupid = self.selectItem("Config Option Lookup", configoptionlookupids)
    if configoptionlookupid != 0:
      self.ovtDB.unlinkConfigOptionLookup(versionedactionid, configoptionlookupid)

  def modifyOption(self, versionedactionid):
    """
    Modify a lookup option relating to the versionedaction
    """
    print " Modify Config Option ".center(80, "-")
    print "Modify option linked to:"
    print self.ovtDB.getVersionedActionName(versionedactionid)
    config = self.ovtDB.getVersionedActionConfig(versionedactionid)

    # Remove anything that is not a lookup option
    ids = {}
    remove = []
    for groupid in config[0]:
      for configoptionid in config[0][groupid]['related'][0]:
        configoption = config[0][groupid]['related'][0][configoptionid]
        ids[configoptionid] = (groupid)
        if not configoption['islookup']:
          remove.append(configoptionid)

    for configoptionid in remove:
      self.dualNestComplete (configoptionid, config, ids)

    self.config['configoptions']['showids'] = ["Config Option"]
    self.viewItems("configoptions", False, config)
    configoptionid = self.selectItem("Config Option", ids)
    values ={}
    if configoptionid != 0:
      configtype = config[0][ids[configoptionid]]['related'][0][configoptionid]['configtype']
      isAutomatic = config[0][ids[configoptionid]]['automatic']
      if not self.askForConfigOptionLookups (values, configtype, allowrequirements=not isAutomatic, allowdefault=False):
        return False
      yn = raw_input("Attach new values to all linked versioned actions? y/[n] ")
      newids = self.ovtDB.addConfigOptionLookups (configoptionid, values)
      if self.checkForYes(yn):
        # Link newids to all versioned actions linked to configoptionid
        versionedactionids = self.ovtDB.simple.getVersionedActionsByConfigOption (configoptionid)
        for configoptionlookupid in newids:
          for vaid in versionedactionids:
            self.ovtDB.createConfigOptionLookupLink(vaid, configoptionlookupid)
      else:
        # Link newids just to current versioned action
        for configoptionlookupid in newids:
          self.ovtDB.createConfigOptionLookupLink(versionedactionid, configoptionlookupid)

  def linkExistingOption(self, versionedactionid, actionid):
    """
    Link an existing option to the specified versioned action
    """
    exit = False
    try:
      while not exit:
        print " Link Config Option".center(80, "-")
        print "Linking option to:"
        print self.ovtDB.getVersionedActionName(versionedactionid)
        print "\n"+magenta("1")+") Search for option and link"
        print magenta("2")+") List options linked to other versions of this action"
        print magenta("0")+") Exit"
        try:
          choice = self.selectItem("Option", range(0,3))
  
          if choice == 0:
            exit = True
          elif choice == 1:
            searchterm = raw_input("Enter search term (% is wildcard): ")
            options = self.ovtDB.searchConfigOptions(searchterm = searchterm)
          elif choice == 2:
            options = self.ovtDB.searchConfigOptions(actionid = actionid)
  
          if not exit:
            self.config['configoptions']['showids'] = ["Config Option"]
            self.viewItems("configoptions", False, options)
            ids = []
            for groupid in options[0]:
              for optionid in options[0][groupid]['related'][0]:
                ids.append(optionid)
            configoptionid = self.selectItem("Config Option", ids)
            if configoptionid != 0:
              # Doesn't matter if the option is already linked or not, ignore result
              self.ovtDB.createConfigOptionLink(versionedactionid, configoptionid)
              # Link all the lookup values
              tempconfig = self.ovtDB.searchConfigOptions(configoptionid=configoptionid)
              opt = tempconfig[0][tempconfig[1][0]]['related'][0][configoptionid]
              if opt['islookup']:
                for configoptionlookupid in opt['related'][0]:
                  result = self.ovtDB.createConfigOptionLookupLink(versionedactionid, configoptionlookupid)
  
        except (ValueError):
          self.error += "Invalid selection"
          continue
    except (EOFError, KeyboardInterrupt):
      pass

  def linkExistingOptionLookup(self, versionedactionid):
    """
    Link an existing option lookup to the specified versioned action
    Only display lookups that are not already linked and are associated with
    options that are linked
    """
    exit = False
    try:
      while not exit:
        configoptionids = []
        nonlookupconfigoptionids = {}
        configoptionlookupids = []
        existingconfigoptionlookupids = {}
        # Find all linked options
        config = self.ovtDB.getVersionedActionConfig(versionedactionid)
        for groupid in config[0]:
          for configoptionid in config[0][groupid]['related'][0]:
            configoptionids.append(configoptionid)
            # Find all linked option lookups
            opt = config[0][groupid]['related'][0][configoptionid]
            if opt['islookup']:
              for configoptionlookupid in opt['related'][0]:
                existingconfigoptionlookupids[configoptionlookupid] = (groupid, configoptionid)

        # Construct a config based on all linked options
        config = ({}, [])
        # Construct a config for all lookups for all linked options
        for configoptionid in configoptionids:
          config = self.ovtDB.searchConfigOptions(configoptionid=configoptionid, extend=config)

        # Find all potential option lookups
        for groupid in config[0]:
          for configoptionid in config[0][groupid]['related'][0]:
            opt = config[0][groupid]['related'][0][configoptionid]
            if opt['islookup']:
              for configoptionlookupid in opt['related'][0]:
                configoptionlookupids.append(configoptionlookupid)
            else:
              nonlookupconfigoptionids[configoptionid] = (groupid)

        # Remove all the config option lookups that are already linked
        for configoptionlookupid in set(existingconfigoptionlookupids.keys()) & set(configoptionlookupids):
          self.tripleNestComplete(configoptionlookupid, config, existingconfigoptionlookupids)
          configoptionlookupids.remove(configoptionlookupid)

        # Remove all the non lookup config options
        for configoptionid in nonlookupconfigoptionids.keys():
          self.dualNestComplete(configoptionid, config, nonlookupconfigoptionids)

        print " Link Config Option Lookup ".center(80, "-")
        print "Linking option lookup to:"
        print self.ovtDB.getVersionedActionName(versionedactionid)

        self.config['configoptions']['showids'] = ["Config Option Lookup"]
        self.viewItems("configoptions", False, config)
        print "\n"+magenta("x")+") Link lookup"
        print magenta("0")+") Exit"
        try:
          choice = self.selectItem("Option Lookup", configoptionlookupids)
  
          if choice == 0:
            exit = True
          else:
            self.ovtDB.createConfigOptionLookupLink(versionedactionid, choice)
  
        except (ValueError):
          self.error += "Invalid selection"
          continue
    except (EOFError, KeyboardInterrupt):
      print ""


  def addConfigOptionGroupExtra(self, values):
    """Get the ordering value for this new option"""
    ordering = raw_input("What position should this group have in the group list? ")
    if not ordering.isdigit():
      self.error += "Not a number, aborted"
      return False
    else:
      values['ordering'] = int(ordering)
      automatic = raw_input("Are all options in this group set at runtime? Yes|[No] ")
      automatic = automatic.lower() 
      values['automatic'] = self.checkForYes(automatic)
      return True

  def askForConfigOptionLookups(self, values, type, allowrequirements, allowdefault = True):
    """
    Interactively fetch a series of lookup values for an option
    """
    done = False
    defaultset = False
    settings = []
    while not done:
      print "Enter a setting name and then a value. An empty name ends the list"
      name = raw_input("Setting name: ")
      if name == "":
        done = True
        continue
      value = raw_input("Value: ")
      if type == "string":
        None
      elif type == "integer":
        if value.isdigit():
          value = int(value)
        else:
          print "Not a number. Try again."
          continue
      elif type == "boolean":
        value = self.checkForYes(value)
      else:
        self.error += "Type not known. Aborted"
        return False

      # Add resource requirements to this lookup option
      if allowrequirements:
        resourceRequirements = raw_input ("Add Resource Requirements? (y/n) ")
        if self.checkForYes(resourceRequirements):
          print "Resource requirements attached to lookup values will only take effect on"
          print "versioned actions that require an attribute from the same resource type."
          print "Select 0 to end the requirments"
          moreRequirements = True
          resourceRequirements = []
  
          while (moreRequirements):
            attributevalueid = self.selectResourceRequirement()
            if attributevalueid == 0:
              moreRequirements = False
            else:
              resourceRequirements.append(attributevalueid)
        else:
          resourceRequirements = []
      else:
        resourceRequirements = []

      if allowdefault:
        default = raw_input("Default? (y/n) ")
        if self.checkForYes(default):
          default = True
          defaultset = True
        else:
          default = False
      else:
        default = False
      settings.append((name, value, resourceRequirements, default))
    if len(settings) == 0:
      self.error += "Aborted"
      return False
    if allowdefault and not defaultset:
      (name, value, resourceRequirements, default) = settings[0]
      settings[0] = (name, value, resourceRequirements, True)
    values['lookups'] = settings
    return True

  def addConfigOptionExtra(self, values):
    """
    Determine what group to add the option to as well as type and ordering
    """
    done = False
    configoptiongroupid = None
    while not done:
      print "Config options are organised by groups."
      print "To choose a group select one of the following options."
      print magenta("1")+") Display groups and select existing group"
      print magenta("2")+") Add new group"
      choice = self.selectItem("Option", range(1,3))
      if choice == 0:
        self.error += "No group... Aborted"
        return False
      elif choice == 1:
        groups = self.ovtDB.getConfigOptionGroups(self.config['configoptiongroups'])
        self.config['configoptiongroups']['showids'] = ["Config Group"]
        self.viewItems("configoptiongroups", False, groups)
        if len(groups[0]) != 0:
          configoptiongroupid = self.selectItem("Config Group", groups[0])
          if configoptiongroupid != 0:
            done = True
      elif choice == 2:
        configoptiongroupid = self.addItem("configoptiongroups")
        if configoptiongroupid == None:
          self.error += "No group... Aborted"
          return False
        else:
          print "Group created and selected"
          done = True
        continue
    values['configoptiongroupid'] = configoptiongroupid

    groups = self.ovtDB.getConfigOptionGroups(self.config['configoptiongroups'])
    isAutomatic = groups[0][configoptiongroupid]['automatic']
    # Now determine the type of option
    self.config['configtypes']['showids'] = ["Type"]
    types = self.viewItems("configtypes")
    configoptiontypeid = self.selectItem(" type of option", types[0])
    if configoptiontypeid == 0:
      self.error += "Aborted"
      return False
    type = types[0][configoptiontypeid]['data']
    values['type'] = type
    values['configoptiontypeid'] = configoptiontypeid
    lookup = raw_input("Does this option have a list of possible settings? (y/[n])")
    lookup = self.checkForYes(lookup)
    values['islookup'] = lookup
    if lookup:
      if not self.askForConfigOptionLookups (values, type, allowrequirements=not isAutomatic):
        return False
    else:
      value = raw_input("Enter default value: ")
      if type == "string":
        None
      elif type == "integer":
        if value.isdigit():
          value = int(value)
        else:
          self.error += "Not a number. Aborted."
          return False
      elif type == "boolean":
        value = self.checkForYes(value)
      else:
        self.error += "Type not known. Aborted"
        return False
      values['defaultvalue'] = value
    # Check whether the value of this option should affect the equivalence calculator
    if isAutomatic:
      equiv = False
    else:
      equiv = raw_input("Does this option significantly affect the behaviour of an action? ([y]/n)")
      if equiv == "":
        equiv = "y"
      equiv = self.checkForYes (equiv)
    values['affectsequivalence'] = equiv
    ordering = raw_input("What position should this option have in the option list? ")
    if not ordering.isdigit():
      self.error += "Invalid number, aborted"
      return False
    values['ordering'] = int(ordering)
    return True

  def createDependency(self, consumer):
    """Creates a dependency from consumer to a producer chosen as part of this function"""

    print " Create Dependency ".center(80, "-")
    print "Consumer: " + self.ovtDB.getVersionedActionName(consumer)
    print "Please select the producer."
    self.findActions()
    try:
      actionid = int(raw_input("Select Action: "))
      search = {"actionid":actionid}
      (actions, ids) = self.ovtDB.searchActions(search, showunavailable=self.showUnavailable)
      if len(actions) != 1:
        self.error += "Action not found"
        return
      self.config['actions']['showids'] = ["Versioned Action"]
      self.printItem("actions", actions[ids[0]])
      producer = int(raw_input("Select Version: "))
      if not producer in actions[ids[0]]['related'][0][actionid]['related'][0]:
        self.error += "Version not found"
        return
      done = False
      dependencygroupid = None
      while not done:
        print "Dependencies are organised by groups. A dependency that is part of a group"
        print "indicates that it is optional, as long as one (and only one) dependency from"
        print "the group has been fulfilled. A dependency with no group indicates the"
        print "dependency must be fulfilled.\n"
        print "To choose a group select one of the following options."
        print magenta("1")+") Display all groups based on the existing dependencies for this consumer"
        print magenta("2")+") Display all groups based on the existing dependencies for this producer"
        print magenta("3")+") Display all groups"
        print magenta("4")+") Add new group"
        print magenta("0")+") Do not assign a group [default]"
        choice = self.selectItem("Option", range(0,5), default=0)
        if choice == 0:
          done = True
          continue
        elif choice == 1:
          groups = self.ovtDB.getDependencyGroups(consumer=consumer)
        elif choice == 2:
          groups = self.ovtDB.getDependencyGroups(producer=producer)
        elif choice == 3:
          groups = self.ovtDB.getDependencyGroups()
        elif choice == 4:
          dependencygroupid = self.addItem("dependencygroups")
          if dependencygroupid == None:
            dependencygroupid = None
          else:
            done = True
          continue
        self.config['dependencygroups']['showids'] = ["Dependency Group"]
        self.viewItems("dependencygroups", False, groups)
        if len(groups[0]) != 0:
          dependencygroupid = self.selectItem("dependencygroups", groups[0])
          if dependencygroupid != 0:
            done = True

      versiononly = raw_input("Is this a weak dependency? (yes, [no]) ")
      versiononly = self.checkForYes (versiononly)

      hostmatch = raw_input("Does this dependency require a host match? (yes, [no]) ")
      hostmatch = self.checkForYes (hostmatch)

    except ValueError:
      self.error += "Invalid selection"
      return
    suggestions = []
    values = {"dependencygroupid":dependencygroupid, "versiononly":versiononly, "hostmatch":hostmatch, "defaultdep":True}
    (success, data) = self.ovtDB.createDependency(consumer=consumer, producer=producer, values = values)
    if success:
      print "Dependency created"
      suggestions.append(data)
    else:
      self.error += data
      return
    if dependencygroupid != None:
      producers = self.ovtDB.getProducersInGroup(dependencygroupid, versiononly)
      self.config['versionedactions']['showids'] = ["Versioned Action"]
      self.viewItems("versionedactions", False, producers)
      versionedactionids = {}
      for actionid in producers[0]:
        for versionedactionid in producers[0][actionid]['related'][0]:
          versionedactionids[versionedactionid] = (actionid)
      removethese = []
      complete = False
      while not complete:
        command = raw_input("Select producers (all | version # [,version #]) [none]: ")
        command = command.replace(" ", "")
        commands = command.split(",")
        fail = False
        for command in commands:
          if command != "all" and \
             command != "none" and \
             (not command.isdigit() or not int(command) in versionedactionids):
            print "The following part of the command did not parse: "+command
            fail = True
        if not fail:
          complete = True
      for command in commands:
        if command == "all":
          for versionedactionid in versionedactionids:
            (success, data) = self.ovtDB.createDependency(consumer=consumer, producer=versionedactionid, values = values)
            if success:
              suggestions.append(data)
              removethese.append(versionedactionid)
            else:
              print "#"*80
              print data
              print "#"*80
        elif command == "none":
          break
        else:
          (success, data) = self.ovtDB.createDependency(consumer=consumer, producer=versionedactionid, values = values)
          if success:
            suggestions.append(data)
            removethese.append(versionedactionid)
          else:
            print "#"*80
            print data
            print "#"*80
    print "WORK NEEDED: deal with the suggestions"

  def createVersion(self, actionid):
    try:
      self.ovtDB.LOCKACTION (actionid) 
      print " Create Version ".center(80, "-")
      print "New version of: "+self.ovtDB.getActionName(actionid)
      newversionedactionid = self.addItem("versionedactions", {"actionid":actionid})
      if newversionedactionid != None:
        # Need to ask if dependencies should be copied etc etc
        search = {"actionid":actionid}
        (actioncategories, ids) = self.ovtDB.searchActions(search, showunavailable=self.showUnavailable)
        self.config['versionedactions']['showids'] = ["Versioned Action"]
        self.viewItems("versionedactions", False, (actioncategories, ids))
        exit = False
        while not exit:
          try:
            versions = actioncategories[ids[0]]['related'][0][actionid]['related']
            versionedactionid = raw_input("Select version to base dependencies on (0 for none): ")
            if versionedactionid != "" and versionedactionid != "0":
              if int(versionedactionid) in versions[0]:
                versionedactionid = int(versionedactionid)
                self.duplicateVersionInformation(actionid, newversionedactionid, versionedactionid)
                exit = True
              else:
                print "Version number not found"
            else:
              exit = True
          except (ValueError):
            print "Not a number, try again!"
        return newversionedactionid
      else:
        self.error += "Cancelled or version already exists!"
    finally:
      self.ovtDB.UNLOCKACTION (actionid) 

  def duplicateVersionInformation(self, actionid, newversionedactionid, versionedactionid):
    # 1) Process the consumers (Those that depend on me)
    # 2) Process the producers (Those I depend on)
    # 3) Process any suggestions made during the session
    # 4) Process the config
    # 5) Process the result fields
    # 6) Process the resource requirements
    # .) DO NOT COMMIT! This will happen ONLY when the 'first' new version command completes
    #    This will be a massive transaction. Almost complete database lock will be in place.

    print " Create Dependencies ".center(80, "-")
    suggestions = []

    # 1) Process the consumers
    self.copyDependencies(versionedactionid, newversionedactionid, "Consumer", suggestions)
    # 2) Process the producers
    self.copyDependencies(versionedactionid, newversionedactionid, "Producer", suggestions)
    # 3) Process any suggestions made during the session
    print "WORK NEEDED: Not processing suggestions yet"
    # 4) Process the config
    self.copyConfig(versionedactionid, newversionedactionid)
    # 5) Process resource requirements
    self.copyResourceRequirements(versionedactionid, newversionedactionid)

  def copyResourceRequirements(self, versionedactionid, newversionedactionid):
    print " Copy Resource Requirements ".center(80, "-")
    resourcerequirements = self.ovtDB.getResourceRequirements(versionedactionid)
    if len(resourcerequirements[0]) == 0:
      print "No resource requirements to copy"
    while len(resourcerequirements[0]) != 0:
      print "Working on: "+self.ovtDB.getVersionedActionName(newversionedactionid)
      newresourcerequirements = self.ovtDB.getResourceRequirements(newversionedactionid)
      self.config['resourcerequirements']['showids'] = []
      self.config['resourcerequirements']['name'] = "Current Resource Requirement"
      self.viewItems("resourcerequirements", False, newresourcerequirements)
      self.config['resourcerequirements']['showids'] = ["Attribute Value"]
      self.config['resourcerequirements']['name'] = "Remaining Resource Requirement"
      self.viewItems("resourcerequirements", False, resourcerequirements)
      attributevalueids = {}
      for typeid in resourcerequirements[0]:
        for attributeid in resourcerequirements[0][typeid]['related'][0]:
          for attributevalueid in resourcerequirements[0][typeid]['related'][0][attributeid]['related'][0]:
            attributevalueids[attributevalueid] = (typeid, attributeid)
      command = raw_input("Enter Command (h - help): ")
      command = command.replace(" ", "")
      commands = command.split(",")
      fail = False
      help = False
      if command == "":
        fail = True
      else:
        for command in commands:
          if command != "h" and \
             command != "help" and \
             command != "all" and \
             command != "iall" and \
             (command[0] != "i" or not command[1:].isdigit() or not int(command[1:]) in attributevalueids) and \
             (not command.isdigit() or not int(command) in attributevalueids):
            print "The following part of the command did not parse: "+command
            fail = True
          if command == "h" or command == "help":
            help = True
      if fail:
        print "Failures during parse, discarding commands"
      elif help:
        print ""
        print "*"*80
        print "To copy resource requirements use the following commands:\n"
        print "all         - all remaining requirements are copied to this new version"
        print "23,45,34,56 - The specified requirements are copied to this new version"
        print "iall        - Ignore all remaining requirements"
        print "i23,i45,i34 - The specified requirements are ignored\n"
        print "The above commands can be chained and will be processed from left to right"
        print "e.g. i24,all - will ignore 24 and copy the rest\n"
        print "Spaces are tolerated and all commands must be comma separated. If any part of"
        print "the command fails to parse the whole command is thrown away"
        print "*"*80
        print ""
      else:
        for command in commands:
          if command == "all":
            removelist = []
            for attributevalueid in attributevalueids:
              result = self.ovtDB.createResourceRequirement(newversionedactionid, attributevalueid)
              if not result:
                print "#"*80
                print "#"+("Requirement #"+str(attributevalueid)+" already present").center(78)+"#"
                print "#"*80
              else:
                removelist.append(attributevalueid)
            for attributevalueid in removelist:
              self.tripleNestComplete(attributevalueid, resourcerequirements, attributevalueids)
          elif command == "iall":
            resourcerequirements = ({}, [])
            attributevalueids = {}
          elif command[0] == "i":
            attributevalueid = int(command[1:])
            if attributevalueid in attributevalueids:
              self.tripleNestComplete(attributevalueid, resourcerequirements, attributevalueids)
          else:
            attributevalueid = int(command)
            if attributevalueid in attributevalueids:
              result = self.ovtDB.createResourceRequirement(newversionedactionid, attributevalueid)
              if not result:
                print "#"*80
                print "#"+("Requirement #"+str(attributevalueid)+" already present").center(78)+"#"
                print "#"*80
              else:
                self.tripleNestComplete(attributevalueid, resourcerequirements, attributevalueids)
      if len(resourcerequirements[0]) != 0:
        print " Copy Resource Requirements ".center(80, "-")

  def copyConfig(self, versionedactionid, newversionedactionid):
    print " Copy configuration ".center(80, "-")
    configuration = self.ovtDB.getVersionedActionConfig(versionedactionid)
    if len(configuration[0]) == 0:
      print "No configuration to copy"
    while len(configuration[0]) != 0:
      print "Working on: "+self.ovtDB.getVersionedActionName(newversionedactionid)
      newconfiguration = self.ovtDB.getVersionedActionConfig(newversionedactionid)
      self.config['configoptions']['showids'] = []
      self.config['configoptions']['name'] = "Current Configuration Option"
      self.viewItems("configoptions", False, newconfiguration)
      self.config['configoptions']['showids'] = ["Config Option"]
      self.config['configoptions']['name'] = "Remaining Configuration Option"
      self.viewItems("configoptions", False, configuration)
      configoptionids = {}
      for groupid in configuration[0]:
        for optionid in configuration[0][groupid]['related'][0]:
          configoptionids[optionid] = (groupid)
      command = raw_input("Enter Command (h - help): ")
      command = command.replace(" ", "")
      commands = command.split(",")
      fail = False
      help = False
      if command == "":
        fail = True
      else:
        for command in commands:
          if command != "h" and \
             command != "help" and \
             command != "all" and \
             command != "iall" and \
             (command[0] != "i" or not command[1:].isdigit() or not int(command[1:]) in configoptionids) and \
             (not command.isdigit() or not int(command) in configoptionids):
            print "The following part of the command did not parse: "+command
            fail = True
          if command == "h" or command == "help":
            help = True
      if fail:
        print "Failures during parse, discarding commands"
      elif help:
        print ""
        print "*"*80
        print "To copy configuration use the following commands:\n"
        print "all         - all remaining options are duplicated to link to this new version"
        print "23,45,34,56 - The specified options are duplicated to link to this new version"
        print "iall        - Ignore all remaining options"
        print "i23,i45,i34 - The specified options are ignored\n"
        print "The above commands can be chained and will be processed from left to right"
        print "e.g. i24,all - will ignore 24 and duplicate the rest\n"
        print "Spaces are tolerated and all commands must be comma separated. If any part of"
        print "the command fails to parse the whole command is thrown away"
        print "*"*80
        print ""
      else:
        for command in commands:
          if command == "all":
            removelist = []
            for configoptionid in configoptionids:
              result = self.ovtDB.createConfigOptionLink(newversionedactionid, configoptionid)
              if not result:
                print "#"*80
                print "#"+("Failed to link config option #"+str(configoptionid)).center(78)+"#"
                print "#"*80
              else:
                # Copy the lookup option links
                opt = configuration[0][configoptionids[configoptionid]]['related'][0][configoptionid]
                if opt['islookup']:
                  for configoptionlookupid in opt['related'][0]:
                    result = self.ovtDB.createConfigOptionLookupLink(newversionedactionid, configoptionlookupid)
                    if not result:
                      print "#"*80
                      print "#"+("Failed to link config option lookup #"+str(configoptionlookupid)).center(78)+"#"
                      print "#"*80
                removelist.append(configoptionid)
            for configoptionid in removelist:
              self.configLinkComplete(configoptionid, configoptionids, configuration)
          elif command == "iall":
            configuration = ({}, [])
            configoptionids={}
          elif command[0] == "i":
            configoptionid = int(command[1:])
            if configoptionid in configoptionids:
              self.configLinkComplete(configoptionid, configoptionids, configuration)
          else:
            configoptionid = int(command)
            if configoptionid in configoptionids:
              result = self.ovtDB.createConfigOptionLink(newversionedactionid, configoptionid)
              if not result:
                print "#"*80
                print "#"+("Failed to link config option #"+str(configoptionid)).center(78)+"#"
                print "#"*80
              else:
                # Copy the lookup option links
                opt = configuration[0][configoptionids[configoptionid]]['related'][0][configoptionid]
                if opt['islookup']:
                  for configoptionlookupid in opt['related'][0]:
                    result = self.ovtDB.createConfigOptionLookupLink(newversionedactionid, configoptionlookupid)
                    if not result:
                      print "#"*80
                      print "#"+("Failed to link config option lookup #"+str(configoptionlookupid)).center(78)+"#"
                      print "#"*80
                self.configLinkComplete(configoptionid, configoptionids, configuration)
      if len(configuration[0]) != 0:
        print (" Copy Configuration ").center(80, "-")

  def configLinkComplete(self, configoptionid, configoptionids, configuration):
    (groupid) = configoptionids[configoptionid]
    del configuration[0][groupid]['related'][0][configoptionid]
    configuration[0][groupid]['related'][1].remove(configoptionid)
    if len(configuration[0][groupid]['related'][0]) == 0:
      del configuration[0][groupid]
      configuration[1].remove(groupid)
    del configoptionids[configoptionid]

  def copyDependencies(self, versionedactionid, newversionedactionid, deptype, suggestions):
    print (" Create "+deptype+" Dependencies ").center(80, "-")
    vadeps = self.ovtDB.getVersionedActionDependencies(versionedactionid, deptype)
    if len(vadeps[0]) == 0:
      print "No "+deptype+" Dependencies to process\n"
    while len(vadeps[0]) != 0:
      print "Working on: "+self.ovtDB.getVersionedActionName(newversionedactionid)
      newvadeps = self.ovtDB.getVersionedActionDependencies(newversionedactionid, deptype, showunavailable=self.showUnavailable)
      self.config['dependencies']['showids'] = []
      self.config['dependencies']['name'] = "Current Dependencies"
      self.viewItems("dependencies", False, newvadeps)
      self.config['dependencies']['showids'] = ["Dependency"]
      self.config['dependencies']['name'] = "Remaining Dependencies"
      self.viewItems("dependencies", False, vadeps)
      dependencyids = {}
      for groupid in vadeps[0]:
        for categoryid in vadeps[0][groupid]['related'][0]:
          for actionid in vadeps[0][groupid]['related'][0][categoryid]['related'][0]:
            for dependencyid in vadeps[0][groupid]['related'][0][categoryid]['related'][0][actionid]['related'][0]:
              dependencyids[dependencyid] = (groupid, categoryid, actionid)
      command = raw_input("Enter Command (h - help): ")
      command = command.replace(" ", "")
      commands = command.split(",")
      fail = False
      help = False
      if command == "":
        fail = True
      else:
        for command in commands:
          if command != "h" and \
             command != "help" and \
             command != "all" and \
             command != "iall" and \
             (command[0] != "i" or not command[1:].isdigit() or not int(command[1:]) in dependencyids) and \
             (command[0] != "n" or not command[1:].isdigit() or not int(command[1:]) in dependencyids) and \
             (not command.isdigit() or not int(command) in dependencyids):
            print "The following part of the command did not parse: "+command
            fail = True
          if command == "h" or command == "help":
            help = True
      if fail:
        print "Failures during parse, discarding commands"
      elif help:
        print ""
        print "*"*80
        print "To duplicate dependencies use the following commands:\n"
        print "all         - all remaining dependencies are duplicated to link to this new"
        print "              version"
        print "23,45,34,56 - The specified dependencies are duplicated to link to this new"
        print "              version"
        print "iall        - Ignore all remaining dependencies"
        print "i23,i45,i34 - The specified dependencies are ignored"
        print "n23,n45     - The specified dependencies are duplicated but require a new"
        print "              version of the consumer. The dependencies are not removed from the"
        print "              pending list as they may need to be ignored or duplicated, which"
        print "              is a user choice. (n23,i23 or n23,23 respectively)\n"
        print "The above commands can be chained and will be processed from left to right"
        print "e.g. i24,n55,all - will ignore 24, create a new version for 55 and duplicate the"
        print "rest\n"
        print "Spaces are tolerated and all commands must be comma separated. If any part of"
        print "the command fails to parse the whole command is thrown away"
        print "*"*80
        print ""
      else:
        for command in commands:
          if command == "all":
            removelist = []
            for dependencyid in dependencyids:
              if deptype == "Consumer":
                (result, data) = self.ovtDB.createDependency(producer=newversionedactionid, dependencyid=dependencyid)
              else:
                (result, data) = self.ovtDB.createDependency(consumer=newversionedactionid, dependencyid=dependencyid)
              if not result:
                print "#"*80
                print "#"+data.center(78)+"#"
                print "#"*80
              else:
                suggestions.extend(data)
                removelist.append(dependencyid)
            for dependencyid in removelist:
              self.quadNestComplete(dependencyid, vadeps, dependencyids)
          elif command == "iall":
            vadeps = ({}, [])
            dependencyids={}
          elif command[0] == "i":
            dependencyid = int(command[1:])
            if dependencyid in dependencyids:
              self.quadNestComplete(dependencyid, vadeps, dependencyids)
          elif command[0] == "n":
            dependencyid = int(command[1:])
            if dependencyid in dependencyids:
              (groupid,categoryid,actionid) = dependencyids[dependencyid]
              print "*"*80
              print "Creating new version of " + vadeps[0][groupid]['related'][0][categoryid]['related'][0][actionid]['data'] +"\n"
              print "A dependency will be created between the new version of the above action and "
              print "the new version of the current action."
              print "You will need to resolve dependencies for the above action before continuing "
              print "with the current action. This process is recursive. Duplicate dependencies will "
              print "safely be ignored. Duplicate dependencies with differing groups or 'Version Only'"
              print "status will be warned about and ignored"
              print "*"*80
              print ""
              newdependencyversionedactionid = self.createVersion(actionid)
              if deptype == "Consumer":
                (result, data) = self.ovtDB.createDependency(producer=newversionedactionid, consumer=newdependencyversionedactionid, dependencyid=dependencyid)
              else:
                (result, data) = self.ovtDB.createDependency(consumer=newversionedactionid, producer=newdependencyversionedactionid, dependencyid=dependencyid)
              if not result:
                print "#"*80
                print "#"+data.center(78)+"#"
                print "#"*80
              else:
                suggestions.extend(data)
          else:
            dependencyid = int(command)
            if dependencyid in dependencyids:
              if deptype == "Consumer":
                (result, data) = self.ovtDB.createDependency(producer=newversionedactionid, dependencyid=dependencyid)
              else:
                (result, data) = self.ovtDB.createDependency(consumer=newversionedactionid, dependencyid=dependencyid)
              if not result:
                print "#"*80
                print "#"+data.center(78)+"#"
                print "#"*80
              else:
                suggestions.extend(data)
                self.quadNestComplete(dependencyid, vadeps, dependencyids)
      if len(vadeps[0]) != 0:
        print (" Create "+deptype+" Dependencies ").center(80, "-")

  def quadNestComplete(self, id, nest, ids):
    (nest1id, nest2id, nest3id) = ids[id]
    del nest[0][nest1id]['related'][0][nest2id]['related'][0][nest3id]['related'][0][id]
    nest[0][nest1id]['related'][0][nest2id]['related'][0][nest3id]['related'][1].remove(id)
    if len(nest[0][nest1id]['related'][0][nest2id]['related'][0][nest3id]['related'][0]) == 0:
      del nest[0][nest1id]['related'][0][nest2id]['related'][0][nest3id]
      nest[0][nest1id]['related'][0][nest2id]['related'][1].remove(nest3id)
      if len(nest[0][nest1id]['related'][0][nest2id]['related'][0]) == 0:
        del nest[0][nest1id]['related'][0][nest2id]
        nest[0][nest1id]['related'][1].remove(nest2id)
        if len(nest[0][nest1id]['related'][0]) == 0:
          del nest[0][nest1id]
          nest[1].remove(nest1id)
    del ids[id]

  def tripleNestComplete(self, id, nest, ids):
    (nest1id, nest2id) = ids[id]
    del nest[0][nest1id]['related'][0][nest2id]['related'][0][id]
    nest[0][nest1id]['related'][0][nest2id]['related'][1].remove(id)
    if len(nest[0][nest1id]['related'][0][nest2id]['related'][0]) == 0:
      del nest[0][nest1id]['related'][0][nest2id]
      nest[0][nest1id]['related'][1].remove(nest2id)
      if len(nest[0][nest1id]['related'][0]) == 0:
        del nest[0][nest1id]
        nest[1].remove(nest1id)
    del ids[id]

  def dualNestComplete(self, id, nest, ids):
    (nest1id) = ids[id]
    del nest[0][nest1id]['related'][0][id]
    nest[0][nest1id]['related'][1].remove(id)
    if len(nest[0][nest1id]['related'][0]) == 0:
      del nest[0][nest1id]
      nest[1].remove(nest1id)
    del ids[id]
