import os
from Action import Action

# QEMU Prebuilt

class A117825(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117825
    self.name = "QEMU Prebuilt"

  # Execute the action.
  def run(self):
    if self.version == "Custom":
      root = self.config.getVariable("Manual QEMU Root")
    elif self.version == "From Toolchain":
      root = self.config.getVariable("Toolchain Root")
    else:
      root = os.path.join (r'/home','overtest','mipsworld','simulator','qemu',self.version)
    self.config.setVariable("QEMU Root", root)
    return self.success()
