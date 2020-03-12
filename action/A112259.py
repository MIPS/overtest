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
from IMGAction import IMGAction

# META Linux uClibc

class A112259(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 112259
    self.name = "META Linux uClibc"

  # Execute the action.
  def run(self):
    """
    Just make a Buildroot compatible patch and pass the patchfile location on
    """
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("LEEDS CVSROOT")
    env = {"CVSROOT":cvsroot}

    if self.version == "Latest":
      tag = "metag"
    else:
      tag = self.version

    buildroot = self.testrun.getVersion ("META Linux Buildroot")
    legacy_git = False

    if buildroot == "METALinux_2_2":
      uclibc_tag = "uclibc_0_9_30_1"
      uclibc_version = "0.9.30.1"
    elif buildroot == "METALinux_2_3":
      uclibc_tag = "uclibc_0_9_30_3"
      uclibc_version = "0.9.30.3"
    elif buildroot in ("METALinux_2_4", "METALinux_2_5"):
      uclibc_tag = ""
      uclibc_base_ref = "master"
      uclibc_metag_ref = "origin/metag"
      uclibc_module = "metag-uClibc"
      uclibc_git = "git://git.le.imgtec.org/metag-uClibc"
      legacy_git = True
    else:
      # Get versions from buildroot
      if not self.gitExport(uri="git://git.le.imgtec.org/buildroot", tag=tag):
        self.error("Failed to export buildroot")

      patch_script = open(os.path.join(self.getWorkPath(),
                                       "buildroot/make-patches.sh"), "r")

      for line in patch_script.readlines():
        if line.startswith("uclibc_version="):
          uclibc_version = line.strip()[15:]
      patch_script.close()
      uclibc_tag = ""
      uclibc_base_ref="refs/tags/v" + uclibc_version
      uclibc_metag_ref="origin/" + uclibc_version + "_metag"
      uclibc_module = "uClibc"
      uclibc_git = "git://git.le.imgtec.org/uClibc"

    if uclibc_tag:
      # CVS
      patchfile = os.path.join(self.getSharedPath(), "uClibc-%s-metag.patch" % uclibc_version)

      exitcode = self.execute(env=env,
                              command=["cvs -q rdiff -ko -u -r %s -r %s metag-uClibc2 | " % (uclibc_tag, tag) +\
                                         "filterdiff -x '*/.config' > %s" % patchfile],
                              shell=True)
    elif legacy_git:
      # Old git repo
      uclibc_dir = os.path.join(self.getWorkPath(), uclibc_module)

      patchfile = os.path.join(self.getSharedPath(), "uClibc.metag.patch")

      # Clone the GIT repository
      exitcode = self.execute(command=[CONFIG.git, "clone", uclibc_git])

      if exitcode == 0:
        exitcode = self.execute(workdir=uclibc_dir,
                                shell=True,
                                command=[("%s diff %s..%s | "+\
                                            "filterdiff -x '*/.config' > %s") % (CONFIG.git, uclibc_base_ref, uclibc_metag_ref, patchfile)])
      else:
        self.error("Failed to clone git repository")
    else:
      # New git repo
      uclibc_dir = os.path.join(self.getWorkPath(), uclibc_module)

      patchfile = os.path.join(self.getSharedPath(), "uClibc-%s-metag.patch" % uclibc_version)

      # Clone the GIT repository
      exitcode = self.execute(command=[CONFIG.git, "clone", uclibc_git])

      if exitcode == 0:
        exitcode = self.execute(workdir=uclibc_dir,
                                shell=True,
                                command=[("%s diff %s..%s | "+\
                                            "filterdiff -x '*/.config' > %s") % (CONFIG.git, uclibc_base_ref, uclibc_metag_ref, patchfile)])

    return (exitcode == 0)
