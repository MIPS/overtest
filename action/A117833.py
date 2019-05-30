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
		 "QEMU":"qemu",
		 "uClibc":"uclibc",
		 "Dejagnu":"dejagnu"}

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
      archive_script = os.path.join (git_dir, "scripts", "archive-source.sh")
      if component == "QEMU" and os.path.exists(archive_script):
        result = self.qemu_archive_source (component, git_dir, prefix, out_file)
      else:
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
        self.error("Unable to compress %s archive" % component)

    return self.success()

  def qemu_archive_source(self, component, git_dir, prefix, out_file):
    workdir=self.testrun.getSharedPath(component)
    archive_dir = os.path.join(workdir, prefix)
    archive_script = os.path.join (git_dir, "scripts", "archive-source.sh")
    archive_out = os.path.join(archive_dir, "qemu.tar")
    os.mkdir(archive_dir)
    result = self.execute(command=[archive_script, archive_out], workdir=git_dir)
    if result != 0:
      self.error("Unable to create %s archive from scripts/archive-source.sh" % component)

    result = self.execute(command=["tar", "-xvf", archive_out], workdir=archive_dir)
    if result != 0:
      self.error("Unable to extract %s archive" % archive_out)

    result = os.remove(archive_out)
    if os.path.exists(archive_out) and result != 0:
      self.error("Unable to remove %s" % archive_out)

    result = self.execute(command=["tar", "-c", prefix, "-f", out_file],
                          workdir=workdir)
    return result
