from utils.TerminalUtilities import *

class Interactive:
  ovtDB=None
  config = {'resources':{"name":"Resource"}, \
            'resourcetypes':{"name":"Resource Type"}, \
            'attributes':{"name":"Attribute"}, \
            'actions':{"name":"Action"}, \
            'versionedactions':{"name":"Versioned Action",\
                                "addcomment": "Version names must begin with major.minor.revision.build numbering "+\
                                              "if this is\nrelevant. Examples as below\n"+\
                                              "'1.2.3.4', '1.2.3', '1.2', '1', '1.2.3.4 some text', '1.2 some text'"}, \
            'dependencies':{"name":"Dependency","allowadd":False},\
            'dependencygroups':{"name":"Dependency Group"},\
            'configoptions':{"name":"Configuration","allowadd":False},\
            'resultfields':{"name":"Result Field","allowadd":False},\
            'resourcerequirements':{"name":"Resource Requirement","allowadd":False},\
            'attributevalues':{"name":"Fixed Resource Attribute","allowadd":False},\
            'configoptions':{"name":"Configuration Option"},\
            'configtypes':{"name":"Config Type"},\
            'configoptiongroups':{"name":"Config Group"},\
            'actioncategories':{"name":"Action Category"}}

  def __init__(self, _ovtDB):
    self.ovtDB = _ovtDB
    self.config['resources']['fetch'] = self.ovtDB.getResources
    self.config['resources']['add'] = self.ovtDB.addResource
    self.config['resourcetypes']['fetch'] = self.ovtDB.getResourceTypes
    self.config['resourcetypes']['add'] = self.ovtDB.addResourceType
    self.config['attributes']['fetch'] = self.ovtDB.getAttributes
    self.config['attributes']['add'] = self.ovtDB.addAttribute
    self.config['actions']['fetch'] = self.ovtDB.searchActions
    self.config['actions']['add'] = self.ovtDB.addAction
    self.config['versionedactions']['add'] = self.ovtDB.addVersionedAction
    self.config['actioncategories']['fetch'] = self.ovtDB.getActionCategories
    self.config['dependencygroups']['add'] = self.ovtDB.addDependencyGroup
    self.config['configtypes']['fetch'] = self.ovtDB.getConfigTypes
    self.config['configoptiongroups']['fetch'] = self.ovtDB.getConfigOptionGroups
    self.config['configoptiongroups']['add'] = self.ovtDB.addConfigOptionGroup
    self.config['configoptions']['add'] = self.ovtDB.addConfigOption
    self.error = ""
    self.info = ""

  def pause(self):
    raw_input("Push enter to continue")

  def checkForYes(self, response):
    """
    Checks the string for a positive response
    """
    return response.lower() in ("y", "ye", "yes", "t", "true")

  def printMessages(self):
    if self.error != None and self.error != "":
      print red(self.error)
    self.error = ""
    if self.info != None and self.info != "":
      print cyan(self.info)
    self.info = ""

  def selectItem(self, itemname, items, default=None):
    exit = False
    while not exit:
      try:
        selection = raw_input("Select "+itemname+": ")
        if selection == "":
          if default != None:
            selection=default
          else:
            continue
        choice = int(selection)
        if choice != 0 and choice not in items:
          raise ValueError()
      except (ValueError):
        print "Invalid selection"
        continue
      exit = True
    return choice

  def viewItems(self, confname, brief = False, (items, ids) = (None,None)):
    conf = self.config[confname]
    if brief:
      print (" List "+conf['name']+"s ").center(80, "-")
    else:
      print (" View "+conf['name']+"s ").center(80, "-")
    if items == None:
      (items,ids) = conf['fetch'](conf)
    if len(ids) == 0:
      print "No "+conf['name']+"s found"
    for id in ids:
      self.printItem(confname, items[id], 0, brief)
    return (items,ids)

  def printItem(self, confname, item, indent = 0, brief = False):
    conf = self.config[confname]
    idtext = ""
    note = ""
    if 'note' in item:
      note=" [%s]" % item['note']
    newindent = indent
    if item['type'] in conf['showids']:
      idtext = magenta(str(item['id']).ljust(7))
      newindent += 7
    print " "*indent+idtext+str(item['data']) + blue(note)
    if brief:
      return
    if "related" in item:
      (items, ids) = item['related']
      if len(items) == 0:
        print " "*(newindent+2)+"No Items"
      for id in ids:
        self.printItem(confname, items[id], newindent+2, brief)

  def addItem(self, confname, values = None):
    if values == None:
      values = {}
    conf = self.config[confname]
    if "allowadd" in conf and not conf['allowadd']:
      print "Not allowed to add "+conf['name']+" entries using generic add"
      return None
    print (" Add "+conf['name']+" ").center(80, "-")
    if "addcomment" in conf:
      print conf['addcomment']
    attributename = raw_input(conf['name']+" Name: ")
    if attributename != "":
      values['name'] = attributename
      if "addextra" in conf:
        if not conf['addextra'](values):
          print "Abort add"
          return None
      print "Creating "+conf['name']+" with default data. Edit as appropriate."
      return conf['add'](values)
    else:
      print "No name supplied"
    return None
