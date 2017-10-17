import os
import glob
from Action import Action

# Toolchain Prebuilt

class A117824(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117824
    self.name = "Toolchain Prebuilt"

  # Execute the action.
  def run(self):
    triple = self.config.getVariable("Manual Triple")
    self.config.setVariable("Triple", triple)
    mips_toolchain = self.config.getVariable("Manual Toolchain Root")

    if mips_toolchain.endswith(".tgz") or mips_toolchain.endswith(".tar.gz"):
      if self.execute(command=["tar", "--strip-components=1",
	                       "-xf", mips_toolchain],
		      workdir=self.getSharedPath()) != 0:
        self.error("Unable to extract toolchain")
      mips_toolchain = self.getSharedPath()

      test_file = os.path.join("bin", "%s-gcc" % triple)
      path1 = os.path.join(self.getSharedPath(), test_file)
      find1 = glob.glob(path1)
      if len(find1) == 1:
	mips_toolchain = self.getSharedPath()
      else:
	path2 = os.path.join(self.getSharedPath(), "*", test_file)
	find2 = glob.glob(path2)
	if len(find2) == 1:
	  mips_toolchain = os.path.dirname(os.path.dirname(find2[0]))
	else:
	  self.error("Cannot locate %s in tarball" % test_file)

    self.config.setVariable("Toolchain Root", mips_toolchain)

    return self.success()
