import os
from Action import Action
from Config import CONFIG
import time
import random
from distutils.version import LooseVersion

# GDB

class A117813(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117813
    self.name = "GDB"

  # Execute the action.
  def run(self):
    branch = self.config.getVariable("GDB Branch")
    remote = self.config.getVariable("GDB Remote")
    gitCmd=[CONFIG.git, "clone",
             "--reference=/projects/mipssw/git/binutils-gdb.git",
             remote,
             "gdb"]
    result = self.execute(workdir=self.getSharedPath(),
                          command=[CONFIG.git, "--version"])
    gitversion = self.fetchOutput().replace("git version ","")
    singleBranch = LooseVersion(gitversion) >= LooseVersion('1.7.10')
    if singleBranch:
      gitCmd += ["--single-branch", "-b", branch]

    # Execute a command overriding some environment variables
    for i in range(30):
      result = self.execute(workdir=self.getSharedPath(), command = gitCmd)
      if result == 0:
	break
      else:
	time.sleep(random.randint(1,30))

    if result != 0:
      self.error("Unable to clone repository")

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "gdb"),
			  command=[CONFIG.git, "config", "core.preloadIndex", "false"])

    if not singleBranch:
      result = self.execute(workdir=os.path.join(self.getSharedPath(), "gdb"),
                            command=[CONFIG.git, "checkout", branch])
      if result != 0:
        self.error("Unable to checkout branch")

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "gdb"),
                          command=[CONFIG.git, "rev-parse", "HEAD"])
    if result == 0:
      self.config.setVariable("GDB rev", self.fetchOutput().strip())
    return self.success()
