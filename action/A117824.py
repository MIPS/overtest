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
