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

# META Linux binutils

class A112258(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 112258
    self.name = "META Linux binutils"

  # Execute the action.
  def run(self):
    """
    Just make a Buildroot compatible patch and pass the patchfile location on
    """
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("LEEDS CVSROOT")
    env = {"CVSROOT":cvsroot}
    patchfile = os.path.join(self.getSharedPath(), "800-metag-binutils.patch")

    if self.version == "Latest":
      tag = "HEAD"
    else:
      tag = self.version

    buildroot = self.testrun.getVersion ("META Linux Buildroot")

    if buildroot == "METALinux_2_2":
      exitcode = self.execute(env=env,
                              command=["cvs -q rdiff -ko -u -r binutils_2_19 -r %s metag-binutils-2.19 > %s" % (tag, patchfile)],
                              shell=True)
    elif buildroot in ("METALinux_2_3", "METALinux_2_4", "METALinux_2_5"):
      exitcode = self.execute(env=env,
                              command=["cvs -q rdiff -ko -u -r binutils_2_20_1 -r %s metag-binutils-2.20 > %s" % (tag, patchfile)],
                              shell=True)
    elif buildroot in ("METALinux_3_0"):
      exitcode = self.execute(env=env,
                              command=["cvs -q rdiff -ko -u -r binutils_2_21 -r %s metag-binutils-2.21 > %s" % (tag, patchfile)],
                              shell=True)

    else:
      # Get versions from buildroot
      if not self.gitExport(uri="git://git.le.imgtec.org/buildroot", tag=tag):
        self.error("Failed to export buildroot")

      patch_script = open(os.path.join(self.getWorkPath(),
                                       "buildroot/make-patches.sh"), "r")

      for line in patch_script.readlines():
        if line.startswith("binutils_version="):
          binutils_version = line.strip()[17:]
          # replace . with _
          binutils_version = binutils_version.replace(".", "_")

      # Binutils moved to git
      binutils_module = "binutils"
      binutils_base_ref = "binutils-%s" % binutils_version
      binutils_metag_ref = "origin/binutils-%s-metag" % binutils_version
      if tag != "HEAD":
            binutils_metag_ref = tag
      binutils_git = "git://git.le.imgtec.org/binutils"
      binutils_dir = os.path.join(self.getWorkPath(), binutils_module)

      # Clone new git repository
      exitcode = self.execute(command=[CONFIG.git, "clone", "--depth", "1", binutils_git])

      if exitcode == 0:
           exitcode = self.execute(workdir=binutils_dir,
                                   shell=True,
                                   command=[("%s diff %s..%s > %s") % (CONFIG.git, binutils_base_ref, binutils_metag_ref, patchfile)])
    return (exitcode == 0)
