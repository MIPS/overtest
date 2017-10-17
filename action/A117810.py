import os
from Action import Action
from IMGAction import IMGAction

# COBIT

class A117810(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117810
    self.name = "COBIT"

  # Execute the action.
  def run(self):
    # Golden version of P4_cmp goes here and should match that in NEOGOLD
    if self.version == "Latest":
      cmp_ver = "2.0.7"
    else:
      cmp_ver = self.version

    COBIT_INST_ROOT = self.neoSelect ("COBIT", select_spec=cmp_ver)

    if COBIT_INST_ROOT is None:
      self.error("Unable to locate COBIT:%s" % cmp_ver)

    self.config.setVariable ("COBIT_INST_ROOT", COBIT_INST_ROOT)
    return True
