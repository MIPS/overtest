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

# vhdl_stork FPGA

class A114202(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 114202
    self.name = "vhdl_stork FPGA"

  # Execute the action.
  def run(self):
    """
    Run the testsuite.
    Tests are taken from the TGZS directory
    """
    return self.neoRunall(VERIFY=self.testrun.getVersion("VerifyToolkit"),
                          PUB=self.config.getVariable("VERIFY_VHDL_STORK_TGZS"),
                          script="python_runall")
