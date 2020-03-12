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

# META Linux GCC

class A112260(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 112260
    self.name = "META Linux GCC"

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
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("LEEDS CVSROOT")
    env = {"CVSROOT":cvsroot};
    patchfile = os.path.join(self.getSharedPath(), "850-metag-gcc.patch")

    if self.version == "Latest":
      if not self.gitExport(uri="git://git.le.imgtec.org/buildroot",
                            tag="metag"):
        self.error("Failed to export buildroot")

      patch_script = open(os.path.join(self.getWorkPath(),
                                       "buildroot/make-patches.sh"), "r")
      for line in patch_script.readlines():
        if line.startswith("gcc_version="):
          tag = line.strip()[12:]
      patch_script.close()
    else:
      tag = "CCS_Gcc2_%s_TAG" % self.version.replace(".", "_")

    exitcode = self.execute(env=env,
                            command=[("cvs -q rdiff -ko -u -r GCC_4_2_4 -r %s metag/tools/gcc2/ | "+\
                                      "filterdiff -x '*/config.sub' -x 'metag/tools/gcc2/dejagnu*' "+\
                                                 "-x 'metag/tools/gcc2/make_source_release' "+\
                                                 "-x 'metag/tools/gcc2/build.mk' "+\
                                                 "-x 'metag/tools/gcc2/check_win32_environment' "+\
                                                 "-x 'metag/tools/gcc2/prepare_slim_multilib' "+\
                                                 " --strip=2 > %s") % (tag, patchfile)],
                            shell=True)

    return (exitcode == 0)

