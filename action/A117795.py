import os
from Action import Action

# ARM Linux Toolchain

class A117795(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117795
    self.name = "ARM Linux Toolchain"

  # Execute the action.
  def run(self):
    self.config.setVariable("ARM_INST_ROOT", self.config.getVariable("Manual ARM Toolkit Root"))
    return True
