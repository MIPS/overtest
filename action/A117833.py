import os
from Config import CONFIG
from Action import Action
import re

# Toolchain Source

component_map = {"GCC":"gcc",
		 "Binutils":"binutils",
		 "GDB":"gdb",
		 "Newlib":"newlib",
		 "SmallClib":"smallclib",
		 "Musl":"musl",
		 "GOLD":"gold",
		 "Glibc":"glibc",
		 "uClibc":"uclibc"}

class A117833(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117833
    self.name = "Toolchain Source"

  # Execute the action.
  def run(self):
    rel_version = self.config.getVariable("Release Version")
    rel_version = re.sub('[^\w\-_\.]', '_', rel_version)
    install_root = self.config.getVariable("Install Root")

    self.createDirectory(install_root)

    for component in component_map:
      if self.testrun.getVersion(component) == None:
	continue
      git_dir = os.path.join(self.testrun.getSharedPath(component), component_map[component])
      prefix = "%s-%s" % (component_map[component], rel_version)
      out_file = os.path.join(self.getWorkPath(),
			      "%s.src.tar" % prefix)
      gzip_file = os.path.join(install_root, "%s.src.tar.gz" % prefix)
      result = self.execute(command=[CONFIG.git, "archive",
				     "--prefix=%s/" % prefix,
				     "--format=tar",
				     "--output=%s" % out_file,
				     "HEAD"],
			    workdir=git_dir)

      if result != 0:
	self.error("Unable to create %s archive" % component)

      result = self.execute(command=["gzip -c %s > %s" % (out_file, gzip_file)], shell=True)

      if result != 0:
        self.error("Unable to comtpress %s archive" % component)

    return self.success()

