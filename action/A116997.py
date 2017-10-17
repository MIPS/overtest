import os
from Action import Action
from IMGAction import IMGAction

# AXD Firmware Build

class A116997(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116997
    self.name = "AXD Firmware Build"

  # Execute the action.
  def run(self):
    METAG_INST_ROOT = self.config.getVariable("METAG_INST_ROOT")

    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("LEEDS CVSROOT")

    # Check out AXD
    result = self.cvsCheckout("axd-firmware", cvsroot=cvsroot)

    if not result:
      self.error("Failed to check out AXD firmware")

    scriptdir = os.path.join(self.getWorkPath(), "axd-firmware")

    env={'FORCE_METAG_INST_ROOT' : METAG_INST_ROOT}

    for script in ["build_mp3", "build_aac"]:
      result = self.execute(command=[os.path.join(".",script)], shell=True, workdir=scriptdir, env=env)

      if result != 0:
        self.error("Failed to build: %s" % script)

    self.config.setVariable('AXD_FIRMWARE_OUTPUT', os.path.join(self.getWorkPath(), "axd-firmware"))

    return True
