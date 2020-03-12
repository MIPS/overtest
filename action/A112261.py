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
from IMGAction import IMGAction
from common.KernelTest import KernelTest
from OvertestExceptions import ConfigException

# META Linux Buildroot

class A112261(Action, IMGAction, KernelTest):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 112261
    self.name = "META Linux Buildroot"
    self.umask = 000

  def buildroot_in_cvs(self, version):
    try:
      if version.startswith("METALinux_2_"):
        minor = int(buildroot[12:])
        if minor <= 5:
          return True
    except ValueError:
      pass
    return False

  # Execute the action.
  def run(self):
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("LEEDS CVSROOT")
    use_git = True

    # Fetch the buildroot module
    if self.version == "Latest":
      tag = "metag"
    else:
      tag = self.version

    if self.buildroot_in_cvs(self.version):
      use_git = False

    if use_git:
      if not self.gitExport(uri="git://git.le.imgtec.org/buildroot", tag=tag,
                            workdir=self.getSharedPath()):
        self.error("Failed to export buildroot")
      module_dir = "buildroot"
    else:
      if not self.cvsCheckout("metag-buildroot2", cvsroot, tag=tag,
                              workdir=self.getSharedPath()):
        self.error("Failed to check out buildroot")
      module_dir = "metag-buildroot2"

    buildroot_dir = os.path.join(self.getSharedPath(), module_dir)

    patch_script = open(os.path.join(self.getSharedPath(),
                                     module_dir, "make-patches.sh"), "r")

    for line in patch_script.readlines():
      if line.startswith("binutils_version="):
        binutils_version = line.strip()[17:]

    if self.version == "METALinux_2_2":
      binutils_version = "2.19.1"
      binutils_path = "toolchain/binutils/%s/"
    elif self.version in ("METALinux_2_3", "METALinux_2_4", "METALinux_2_5"):
      binutils_version = "2.20.1"
      binutils_path = "toolchain/binutils/%s/"
    elif self.version in ("METALinux_3_0"):
      binutils_version = "2.21"
      binutils_path = "package/binutils/binutils-%s/"
    elif self.version in ("METALinux_3_2_p1"):
      binutils_version = "2.23.2"
      binutils_path = "package/binutils/%s/"
    else:
      binutils_path = "package/binutils/%s/"

    # Apply the META patches
    if self.execute(workdir=buildroot_dir,
                    shell=True, 
                    command=["cp "+
                             ("%s/*.patch " % self.testrun.getSharedPath("META Linux binutils")) +
                             binutils_path % binutils_version]) != 0:
      self.error("Failed to apply binutils patch")

    if self.execute(workdir=buildroot_dir,
                    shell=True, 
                    command=["cp "+
                             ("%s/*.patch " % self.testrun.getSharedPath("META Linux GCC")) +
                             "toolchain/gcc/4.2.4/"]) != 0:
      self.error("Failed to apply GCC patch")

    if self.execute(workdir=buildroot_dir,
                    shell=True, 
                    command=["cp "+
                             ("%s/*.patch " % self.testrun.getSharedPath("META Linux uClibc")) +
                             "toolchain/uClibc/"]) != 0:
      self.error("Failed to apply uClibc patch")

    if self.version == "METALinux_2_2":
      if self.execute(workdir=buildroot_dir,
                      shell=True, 
                      command=["cp "+
                               ("%s/*.patch " % self.testrun.getSharedPath("META Linux BusyBox")) +
                               "package/busybox/"]) != 0:
        self.error("Failed to apply BusyBox patch")

    if self.execute(workdir=buildroot_dir,
                    shell=True, 
                    command=["cp "+
                             ("%s/*.patch " % self.testrun.getSharedPath("META Linux Kernel")) +
                             "toolchain/kernel-headers/"]) != 0:
      self.error("Failed to apply kernel patch")

    buildroot_defconfig, buildroot_options = self.getBuildrootConfigAndOptions()

    # Build
    if self.execute(workdir=buildroot_dir,
                    command=["make", buildroot_defconfig]) != 0:
      self.error("Failed to rebuild the existing config")

    build_cmd = ["make"]
    build_cmd += buildroot_options
    if self.execute(workdir=buildroot_dir,
                    command=build_cmd) != 0:
      self.error("Failed to build buildroot")

    # Remove the fakeroot so buildroot can be moved
    if self.version == "METALinux_2_2":
      if self.execute(workdir=buildroot_dir,
                      command=["rm", "-rf", "./build_metag/fakeroot-1.9.5-host"]) != 0:
        self.error("Failed to remove fakeroot")
    else:
      if self.execute(workdir=buildroot_dir,
                      shell=True, 
                      command=["rm -rf ./output/build/host-fakeroot-*"]) != 0:
        self.error("Failed to remove fakeroot")

    # Tar up the build tree
    if self.execute(command=["tar", "-czf", "%s.tgz" % module_dir, module_dir], workdir=self.getSharedPath()) != 0:
      self.error("Failed to tar up build tree")

    return True
