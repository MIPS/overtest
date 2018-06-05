import os
from Action import Action
from Config import CONFIG
import time
import random

# Binutils

class A117815(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117815
    self.name = "Binutils"

  # Execute the action.
  def run(self):
    branch = self.config.getVariable("Binutils Branch")
    remote = self.config.getVariable("Binutils Remote")
    # Execute a command overriding some environment variables
    for i in range(3):
      result = self.execute(workdir=self.getSharedPath(),
			    command=[CONFIG.git, "clone",
						 "--reference=/projects/mipssw/git/binutils-gdb.git",
						 remote,
						 "binutils"])
      if result == 0:
	break
      else:
	time.sleep(random.randint(1,10))

    if result != 0:
      self.error("Unable to clone repository")

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "binutils"),
			  command=[CONFIG.git, "config", "core.preloadIndex", "false"])

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "binutils"),
			  command=[CONFIG.git, "checkout", branch])

    if result != 0:
      self.error("Unable to checkout branch")

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "binutils"),
			  command=[CONFIG.git, "rev-parse", "HEAD"])
    if result == 0:
      self.config.setVariable("Binutils rev", self.fetchOutput().strip())

    return self.success()
