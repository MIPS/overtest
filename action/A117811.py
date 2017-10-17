import os
from Action import Action
from common.MIPSTools import MIPSConfig
from Config import CONFIG

# mips_tool_chain

class A117811(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117811
    self.name = "mips_tool_chain"

  # Execute the action.
  def run(self):
    if self.version == "Portal":
      branch = self.config.getVariable("mips_tool_chain Branch")

      ret = self.execute(command=[CONFIG.git, "clone", "%s:mips_tool_chain.git" % MIPSConfig.Portal],
                         workdir=self.getWorkPath())

      if ret != 0:
        self.error("Unable to clone")

      ret = self.execute(command=[CONFIG.git, "checkout", branch],
                         workdir=os.path.join(self.getWorkPath(), "mips_tool_chain"))

      if ret != 0:
        self.error("Unable to checkout")

      ret = self.execute(command=["./make_workarea %s" % self.getSharedPath()],
                         workdir=os.path.join(self.getWorkPath(),
                                              "mips_tool_chain", "build_scripts"),
                         shell=True)
    else:
      self.error("Unknown version: %s" % self.version)

    return ret == 0
