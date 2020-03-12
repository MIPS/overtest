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
from Config import CONFIG

# META Linux Kernel

class A112256(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 112256
    self.name = "META Linux Kernel"

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
    """
    Just make a Buildroot compatible patch and pass the patchfile location on
    """

    buildroot = self.testrun.getVersion ("META Linux Buildroot")
    use_git = True

    if buildroot == "Latest":
      tag = "metag"
    else:
      tag = buildroot

    if self.buildroot_in_cvs(buildroot):
      use_git = False

    host = self.getResource("Execution Host")

    if use_git:
      if not self.gitExport(uri="git://git.le.imgtec.org/buildroot", tag=tag):
        self.error("Failed to export buildroot")

      patch_script = open(os.path.join(self.getWorkPath(),
                                       "buildroot/make-patches.sh"), "r")
    else:
      cvsroot = host.getAttributeValue("LEEDS CVSROOT")

      if not self.cvsCheckout(module="metag-buildroot2/make-patches.sh",
                              cvsroot=cvsroot, tag=tag):
        self.error("Failed to checkout make-patches")

      patch_script = open(os.path.join(self.getWorkPath(),
                                       "metag-buildroot2/make-patches.sh"), "r")

    for line in patch_script.readlines():
      if line.startswith("kernel_version="):
        kernel_version = line.strip()[15:]
      elif line.startswith("kernel_patch_version="):
        kernel_patch_version = line.strip()[21:]
    patch_script.close()

    if buildroot == "METALinux_2_2":
      kernel_full_version = "%s.%s" % (kernel_version, kernel_patch_version)
    else:
      kernel_full_version = "%s%s" % (kernel_version, kernel_patch_version)

    kernel_base_ref = "refs/tags/v%s" % kernel_version
    kernel_module = "metag-linux-2.6"

    if self.version == "git-uri":
      kernel_metag_ref = "%s" % self.config.getVariable("branch-name")
      kernel_git = "%s" % self.config.getVariable("uri")
    else:
      kernel_git = "git://git.le.imgtec.org/metag-linux-2.6"
      if self.version == "Latest":
        kernel_metag_ref = "origin/metag"
      else:
        kernel_metag_ref = "refs/tags/%s" % self.version

    patchfile = os.path.join(self.getSharedPath(), "linux-%s-metag.patch" % kernel_full_version)
    kernel_dir = os.path.join(self.getWorkPath(), kernel_module)

    # Clone the GIT repository
    exitcode = self.execute(command=[CONFIG.git, "clone", "--depth", "1", kernel_git])

    # Process the arch/metag directories
    if exitcode == 0:
      exitcode = self.execute(workdir=kernel_dir,
                              shell=True,
                              command=[("%s diff %s %s | "+\
                                        "filterdiff -i '*/arch/metag/*' > %s") % (CONFIG.git, kernel_base_ref, kernel_metag_ref, patchfile)])
    else:
      self.error("Failed to clone git repository")

    # Process the asm-generic directories
    if exitcode == 0:
      if use_git:
        # filter out conflicting changes to asm/poll.h
        extra_filter = "-x '*/include/asm-generic/poll.h'"
      else:
        extra_filter = ""
      exitcode = self.execute(workdir=kernel_dir,
                              shell=True,
                              command=[("%s diff %s %s | "+\
                                        "filterdiff -i '*/include/asm-generic/*' %s >> %s") % (CONFIG.git, kernel_base_ref, kernel_metag_ref, extra_filter, patchfile)])
    else:
      self.error("Failed to get arch/metag patch")

    # Check patch generation succeeded
    if exitcode != 0:
      self.error("Failed to get asm-generic patch")

    # Check out the kernel
    if exitcode == 0:
      exitcode = self.execute(workdir=kernel_dir,
                              command=[CONFIG.git, "checkout", kernel_metag_ref]) != 0

    if exitcode == 0:
      tgz_file = os.path.join(self.getSharedPath(), "%s.tgz" %kernel_module)
      if self.execute(command=["tar", "-czf", tgz_file, kernel_module]) != 0:
        self.error("Failed to create kernel tarball")

    return True

