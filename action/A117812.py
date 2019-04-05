import os
from Action import Action
from Config import CONFIG

# GCC

class A117812(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117812
    self.name = "GCC"

  # Execute the action.
  def run(self):
    self.gitFetch("gcc.git")

    # Don't care if this fails.  It is present to fix a timing issue in checkout
    # where a pragma test is sensitive to time stamps.
    self.execute(workdir=os.path.join(self.getSharedPath(), self.name.lower()),
		 command=["touch", "gcc/testsuite/gcc.dg/cpp/_Pragma3.c"])

    if "override" in self.version:
      override_list = self.config.getVariable(self.name + " Override").split(",")
      for override in override_list:
	if override == "":
	  continue
	if ":" in override:
	  commit, file = override.split(":")
	  result = self.execute(workdir=os.path.join(self.getSharedPath(), self.name.lower()),
				command=[CONFIG.git, "checkout", commit, file])
	  if result != 0:
	    self.error("Unable to checkout %s:%s" % (commit, file))
	else:
	  result = self.execute(workdir=os.path.join(self.getSharedPath(), self.name.lower()),
				command=[CONFIG.git, "cherry-pick", override])
	  if result != 0:
	    self.error("Unable to cherry-pick %s" % (override))


    return self.success()
