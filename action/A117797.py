import os
from Action import Action
from IMGAction import IMGAction
from OvertestExceptions import ConfigException

# GccMinGW

class A117797(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117797
    self.name = "GccMinGW"

  # Execute the action.
  def run (self):
    # GccMinGW does not support patching but does allow alternate roots to be provided
    # both within or outside of neo
    toolkit_root = ""
    try:
      toolkit_root = self.config.getVariable ("Manual GccMinGW Root")
    except ConfigException:
      # Manual toolkit root not supported
      pass
    GCCMINGW_ROOT = None

    if toolkit_root == "":
      toolkit_root = "root"

    # Paths can be absolute and hence not be in neo. 
    if not toolkit_root.startswith(os.sep):
      self.config.setVariable ("GccMinGW Toolkit Root", toolkit_root)
      GCCMINGW_ROOT = self.neoSelect ("GccMinGW", self.version, root=toolkit_root)
      if GCCMINGW_ROOT == None:
        self.error("GCCMinGW Toolkit %s/%s not found"% (self.version,toolkit_root))
      self.registerLogFile (os.path.join (GCCMINGW_ROOT, ".neo.txt")) 
    else:
      self.config.setVariable ("GccMinGW Toolkit Root", "scratch")
      GCCMINGW_ROOT = toolkit_root

    self.config.setVariable ("GCCMINGW_ROOT", GCCMINGW_ROOT)
    return True
