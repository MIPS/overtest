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
from OvertestExceptions import ConfigException
from parsers.GCC4Regression import GCC4RegressionParser
import re
import glob

# GAS Test

class A117838(Action, GCC4RegressionParser):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117838
    self.name = "GAS Test"

  # Execute the action.
  def run(self):
    binutils = os.path.join(self.testrun.getSharedPath("Binutils"), "binutils")
    dejagnu = os.path.join(self.testrun.getSharedPath("Dejagnu"), "dejagnu")
    triple = self.config.getVariable("Triple")

    # Create the site config to run the suite
    self.make_site(binutils, triple)

    toolchain_root = self.config.getVariable("Toolchain Root")

    env = {}
    env['PATH'] = CONFIG.makeSearchPath([os.path.join(toolchain_root, "bin"),
					dejagnu, os.environ['PATH']])
    env['LC_ALL'] = 'C'
    try:
      arch = self.config.getVariable("Architecture")
    except ConfigException, e:
      arch = "mips"

    target_board = arch + "-sim-mti32"
    cmd = ["runtest", "--tool", "gas", "--target_board=%s" % target_board]
    self.execute(env=env, command=cmd)

    self.registerLogFile(os.path.join (self.getWorkPath(), "gas.log"), compress=True)
    self.registerLogFile(os.path.join (self.getWorkPath(), "gas.sum"), compress=True)

    summary = self.parse (os.path.join (self.getWorkPath(), "gas.log"))

    return self.success(summary)

  def make_site(self, src, triple):
    a = """set host_triplet x86_64-pc-linux-gnu
	   set target_alias %s
	   set target_triplet %s
	   set build_triplet x86_64-pc-linux-gnu
	   set srcdir %s/gas/testsuite
	   set objdir %s
	   set AS %s-as
	   set OBJDUMP %s-objdump
	   set OBJCOPY %s-objcopy
	   set READELF %s-readelf
	   set NM %s-nm
	   set ADDR2LINE %s-addr2line"""

    canon_triple = triple
    if triple.startswith("nanomips"):
      canon_triple = triple.replace("nanomips-", "nanomips-unknown-")
    a = a % (triple,canon_triple,src,self.getWorkPath(),triple,triple,triple,triple,triple,triple)
    with open(os.path.join(self.getWorkPath(), "site.exp"), "w") as fh:
      fh.write(a)
