import os
from Action import Action
from Config import CONFIG
import time
import random

# GOLD

class A117834(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117834
    self.name = "GOLD"

  # Execute the action.
  def run(self):
    branch = self.config.getVariable("GOLD Branch")
    remote = self.config.getVariable("GOLD Remote")
    # Execute a command overriding some environment variables
    for i in range(30):
      result = self.execute(workdir=self.getSharedPath(),
			    command=[CONFIG.git, "clone",
						 "--reference=/projects/mipssw/git/binutils-gdb.git",
						 remote,
						 "gold"])
      if result == 0:
	break
      else:
	time.sleep(random.randint(1,30))

    if result != 0:
      self.error("Unable to clone repository")

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "gold"),
			  command=[CONFIG.git, "config", "core.preloadIndex", "false"])

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "gold"),
			  command=[CONFIG.git, "checkout", branch])

    if result != 0:
      self.error("Unable to checkout branch")

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "gold"),
                          command=[CONFIG.git, "rev-parse", "HEAD"])
    if result == 0:
      self.config.setVariable("GOLD rev", self.fetchOutput().strip())
    return self.success()
