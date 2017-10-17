import os
from action.Action import Action
from action.IMGAction import IMGAction
from Config import CONFIG
from OvertestExceptions import ConfigException

# NeoBuild
class NeoBuild(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)

  # Execute the action.
  def run(self):
    if self.version in ["Tag", "Latest"]:
      host = self.getResource("Execution Host")
      cvsroot = host.getAttributeValue("KL metag CVSROOT")

      ccs_version = ":MAX"
      head = True
      if self.version == "Tag" and self.config.getVariable("%s Tag" % self.name) != "":
        ccs_version = self.config.getVariable("%s Tag" % self.name)
        head = False

      self.error("About to access KL metag CVS repository. Please fix action")
      if not self.ccsCheckout(self.ccsfile,
                              self.name,
                              ccs_version,
                              cvsroot):
        self.error("Unable to check out %s:%s" % (self.name, ccs_version))

      if head:
        # Now update to cvs HEAD
        env = {}
        env['CVSROOT'] = cvsroot
        result = self.execute(command=[CONFIG.cvs, "update", "-A", "metag/tools"],
                              env=env)
        if result != 0:
          self.error("Unable to update to HEAD")

      # Build
      env = {}
      env['METAG_INST_ROOT'] = self.getSharedPath()
      env['NEW_INST_ROOT'] = self.getSharedPath()

      if "x64" in self.config.getVariable("%s Build" % self.name):
        env['NEOBUILD'] = "x64"
      elif "x32" in self.config.getVariable("%s Build" % self.name):
        env['NEOBUILD'] = "x32"
      elif "x86_64" in host.getAttributeValues("Processor"):
        env['NEOBUILD'] = "x64"
      else:
        env['NEOBUILD'] = "x32"

      scripts=os.path.join(self.getWorkPath(), "metag", "tools", "scripts")
      tools_quick="./tools_quick"
      tools_quick += " clean"
      debug = False
      try:
        debug = debug or self.config.getVariable("%s Debug" % self.name)
      except ConfigException:
        pass

      if debug or self.config.getVariable("MetaMtxToolkit Debug"):
        tools_quick += " debug"
      tools_quick += " %s" % self.name
      result = self.execute(command=[tools_quick], shell=True,
                            workdir=scripts, env=env)

      if result != 0:
        self.error("Unable to build %s" % self.name)

    return True
