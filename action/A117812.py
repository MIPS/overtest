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

# GCC

class A117812(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117812
    self.name = "GCC"

  # Execute the action.
  def run(self):
    self.gitFetch("gcc.git")

    # Don't care if this fails.  It is present to fix a timing issue in checkout
    # where a pragma test is sensitive to time stamps.
    self.execute(workdir=os.path.join(self.getSharedPath(), self.name.lower()),
		 command=["touch", "gcc/testsuite/gcc.dg/cpp/_Pragma3.c"])

    if "override" in self.version:
      override_list = self.config.getVariable(self.name + " Override").split(",")
      for override in override_list:
	if override == "":
	  continue
	if ":" in override:
	  commit, file = override.split(":")
	  result = self.execute(workdir=os.path.join(self.getSharedPath(), self.name.lower()),
				command=[CONFIG.git, "checkout", commit, file])
	  if result != 0:
	    self.error("Unable to checkout %s:%s" % (commit, file))
	else:
	  result = self.execute(workdir=os.path.join(self.getSharedPath(), self.name.lower()),
				command=[CONFIG.git, "cherry-pick", override])
	  if result != 0:
	    self.error("Unable to cherry-pick %s" % (override))


    return self.success()
