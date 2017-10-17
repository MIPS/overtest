import os
from Action import Action
from IMGAction import IMGAction
from OvertestExceptions import ConfigException

# MECCToolkit

class A113857(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 113857
    self.name = "MECCToolkit"

  # Execute the action.
  def run(self):
    # MECC does not support patching but does allow alternate roots to be provided
    # both within or outside of neo
    toolkit_root = ""
    try:
      toolkit_root = self.config.getVariable ("Manual MECC Toolkit Root")
    except ConfigException:
      # Manual toolkit root not supported
      pass
    MECC_INST_ROOT = None

    if toolkit_root == "":
      toolkit_root = "root"

    # Paths can be absolute and hence not be in neo. 
    if not toolkit_root.startswith(os.sep):
      self.config.setVariable ("MECC Toolkit Root", toolkit_root)
      MECC_INST_ROOT = self.neoSelect ("MECCToolkit", self.version, root=toolkit_root)
      if MECC_INST_ROOT == None:
        self.error("MECC Toolkit %s/%s not found"% (self.version,toolkit_root))
      self.registerLogFile (os.path.join (MECC_INST_ROOT, ".neo.txt")) 
    else:
      self.config.setVariable ("MECC Toolkit Root", "scratch")
      MECC_INST_ROOT = toolkit_root

    self.config.setVariable ("MECC_INST_ROOT", MECC_INST_ROOT)
    return True
