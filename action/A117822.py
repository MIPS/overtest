#  Copyright (C) 2012-2020 MIPS Tech LLC
#  Written by Matthew Fortune <matthew.fortune@imgtec.com> and
#  Daniel Sanders <daniel.sanders@imgtec.com>
#  This file is part of Overtest.
#
#  Overtest is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3, or (at your option)
#  any later version.
#
#  Overtest is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with overtest; see the file COPYING.  If not, write to the Free
#  Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
#  02110-1301, USA.
import os
from Action import Action
from Config import CONFIG
import glob
import time
import random

# QEMU Build

class A117822(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117822
    self.name = "QEMU Build"

  # Execute the action.
  def run(self):
    # Execute a command overriding some environment variables
    for i in range(30):
      result = self.execute(command=[CONFIG.git, "clone",
                                     "--reference=%s/mips_tool_chain.git" % CONFIG.git,
                                     "--branch=master",
                                     "%s/mips_tool_chain.git" % CONFIG.gitremote,
                                     "mips_tool_chain"])
      if result == 0:
	break
      else:
	time.sleep(random.randint(1,30))

    if result != 0:
      self.error("Unable to clone repository")

    # Now construct the work area
    result = self.execute(command=["build_scripts/make_workarea %s %s" % (self.getWorkPath(), CONFIG.gitremote)],
			  workdir=os.path.join(self.getWorkPath(), "mips_tool_chain"),
			  shell=True)
    if result != 0:
      self.error("Unable to make work area")

    result = self.execute(command=[CONFIG.git, "checkout", "master"],
			  workdir=os.path.join(self.getWorkPath(), "src", "mips_tool_chain"))

    if result != 0:
      self.error("Unable to change branch")

    targets = []
    if self.version in ("All", "Linux User"):
      targets.append("mips-linux-user")
      targets.append("mipsel-linux-user")
      targets.append("mipsn32-linux-user")
      targets.append("mipsn32el-linux-user")
      targets.append("mips64-linux-user")
      targets.append("mips64el-linux-user")

    if self.version in ("All", "System"):
      targets.append("mipsel-softmmu")
      targets.append("mips-softmmu")
      targets.append("mips64el-softmmu")
      targets.append("mips64-softmmu")

    install = os.path.join(self.getSharedPath(), "install-qemu")
    installtgz = None
    manual_install = self.config.getVariable("Install Root")
    if manual_install != "":
      if manual_install.endswith(".tgz") or manual_install.endswith(".tar.gz"):
	installtgz = manual_install
      else:
	install = manual_install
    hostinstall = os.path.join(self.getSharedPath(), "hostinstall-qemu")
    self.config.setVariable("QEMU Root", install)

    build = os.path.join(self.getWorkPath(), "obj-qemu")

    options = ["--git_home=%s" % CONFIG.gitremote,
	       "--prefix=%s" % hostinstall,
	       "--hostlibs=%s" % hostinstall,
	       "--jobs=%d" % self.concurrency]

    for pkg in ["zlib", "pixman", "libffi", "glib"]:
      location = glob.glob(os.path.join(self.testrun.getSharedPath("Packages"), "packages", "%s*" % pkg))
      if len(location) != 1:
        self.error("Could not locate %s package" % pkg)
      options.append("--src=%s:%s" % (pkg, location[0]))

    cmd = ["b/build_toolchain", "update"]
    cmd.extend(options)

    if self.execute(command=[" ".join(cmd + ["zlib", "pixman", "libffi", "glib"])], shell=True) != 0:
      self.error("Failed to unpack support libraries")

    cmd = ["b/build_toolchain", "build"]
    cmd.extend(options)
    if self.execute(command=[" ".join(cmd + ["zlib"])], shell=True) != 0:
      self.error("Failed to build zlib")

    if self.execute(command=[" ".join(cmd + ["pixman"])], shell=True) != 0:
      self.error("failed to build pixman")

    if self.execute(command=[" ".join(cmd + ["libffi"])], shell=True) != 0:
      self.error("failed to build libffi")

    if self.execute(command=[" ".join(cmd + ["glib"])], shell=True) != 0:
      self.error("Failed to build glib")

    options = ["--path=%s" % os.path.join(install, "bin"),
	       "--git_home=%s" % CONFIG.gitremote,
	       "--build=%s" % build,
	       "--prefix=%s" % install,
	       "--target=mips-elf",
	       "--extra_config_opts=--target-list=%s" % ",".join(targets),
	       "--hostlibs=%s" % hostinstall,
	       "--jobs=%d" % self.concurrency]

    qemu = os.path.join(self.testrun.getSharedPath("QEMU"), "qemu")
    options.append("--src=qemu:%s" % qemu)

    cmd = ["b/build_toolchain", "build"]
    cmd.extend(options)
    if self.execute(command=[" ".join(cmd + ["qemu"])], shell=True) != 0:
      self.error("Failed to build qemu")

    if installtgz != None:
      foldername = os.path.basename(installtgz).split(".", 1)[0]
      if self.execute(command=["tar", "-czf", installtgz,
	                       "--transform=s|^[^/]*/|%s/|" % foldername,
	                       os.path.basename(install)],
		      workdir=self.getSharedPath()) != 0:
        self.error("Failed to tar up toolchain")
		      
    return self.success()
