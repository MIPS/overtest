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
from common.MIPSTools import MIPSConfig
from Config import CONFIG
import time
import random

# mips_tool_chain

class A117811(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117811
    self.name = "mips_tool_chain"

  # Execute the action.
  def run(self):
    if self.version == "Portal":
      branch = self.config.getVariable("mips_tool_chain Branch")

      for i in range(30):
        ret = self.execute(command=[CONFIG.git, "clone", "%s:mips_tool_chain.git" % MIPSConfig.Portal],
                           workdir=self.getWorkPath())
        if result == 0:
          break
        else:
          time.sleep(random.randint(1,30))

      if ret != 0:
        self.error("Unable to clone")

      ret = self.execute(command=[CONFIG.git, "checkout", branch],
                         workdir=os.path.join(self.getWorkPath(), "mips_tool_chain"))

      if ret != 0:
        self.error("Unable to checkout")

      ret = self.execute(command=["./make_workarea %s" % self.getSharedPath()],
                         workdir=os.path.join(self.getWorkPath(),
                                              "mips_tool_chain", "build_scripts"),
                         shell=True)
    else:
      self.error("Unknown version: %s" % self.version)

    return ret == 0
