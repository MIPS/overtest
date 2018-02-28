import os
from Action import Action
from Config import CONFIG
import time
import random

# GCC

class A117812(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117812
    self.name = "GCC"

  # Execute the action.
  def run(self):
    branch = self.config.getVariable("GCC Branch")
    remote = self.config.getVariable("GCC Remote")
    # Execute a command overriding some environment variables
    for i in range(3):
      result = self.execute(workdir=self.getSharedPath(),
			    command=[CONFIG.git, "clone",
						 "--reference=/projects/mipssw/git/gcc.git",
						 remote,
						 "gcc"])
      if result == 0:
	break
      else:
	time.sleep(random.randint(1,10))

    if result != 0:
      self.error("Unable to clone repository")


    result = self.execute(workdir=os.path.join(self.getSharedPath(), "gcc"),
			  command=[CONFIG.git, "config", "core.preloadIndex", "false"])

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "gcc"),
			  command=[CONFIG.git, "checkout", branch])

    if result != 0:
      self.error("Unable to checkout branch")

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "gcc"),
	                  command=[CONFIG.git, "rev-parse", "HEAD"])
    if result == 0:
      self.config.setVariable("GCC rev", self.fetchOutput())

    # Don't care if this fails.  It is present to fix a timing issue in checkout
    # where a pragma test is sensitive to time stamps.
    self.execute(workdir=os.path.join(self.getSharedPath(), "gcc"),
		 command=["touch", "gcc/testsuite/gcc.dg/cpp/_Pragma3.c"])

    if "override" in self.version:
      override_list = self.config.getVariable("GCC Override").split(",")
      for override in override_list:
	try:
	  commit, file = override.split(":")
	except ValueError:
	  self.error("Unknown override %s"% override)
	result = self.execute(workdir=os.path.join(self.getSharedPath(), "gcc"),
			      command=[CONFIG.git, "checkout", commit, file])
	if result != 0:
	  self.error("Unable to checkout %s:%s" % (commit, file))

    return self.success()
