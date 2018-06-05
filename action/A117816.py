import os
from Action import Action
from Config import CONFIG
import time
import random

# Dejagnu

class A117816(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117816
    self.name = "Dejagnu"

  # Execute the action.
  def run(self):
    branch = self.config.getVariable("Dejagnu Branch")
    remote = self.config.getVariable("Dejagnu Remote")
    # Execute a command overriding some environment variables
    for i in range(3):
      result = self.execute(workdir=self.getSharedPath(),
			    command=[CONFIG.git, "clone",
						 "--reference=/projects/mipssw/git/dejagnu.git",
						 remote,
						 "dejagnu"])
      if result == 0:
	break
      else:
	time.sleep(random.randint(1,10))

    if result != 0:
      self.error("Unable to clone repository")

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "dejagnu"),
			  command=[CONFIG.git, "config", "core.preloadIndex", "false"])

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "dejagnu"),
			  command=[CONFIG.git, "checkout", branch])

    if result != 0:
      self.error("Unable to checkout branch")

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "dejagnu"),
	                  command=[CONFIG.git, "rev-parse", "HEAD"])
    if result == 0:
      self.config.setVariable("Dejagnu rev", self.fetchOutput().strip())

    return self.success()
