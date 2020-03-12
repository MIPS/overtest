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

# Binutils Build

class A117820(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117820
    self.name = "Binutils Build"

  # Execute the action.
  def run(self):
    binutils = os.path.join(self.testrun.getSharedPath("Binutils"), "binutils")
    dejagnu = os.path.join(self.testrun.getSharedPath("Dejagnu"), "dejagnu")
    target = self.config.getVariable("Target")
    configure = os.path.join(binutils, "configure")
    env = { 'PATH': CONFIG.makeSearchPath([dejagnu,
	    "/user/rgi_data2/Verify/CentOS-5/Tcl_8.6.4_x64/root/bin",
	    os.environ['PATH']])}
    if self.execute(command=["%s --target=%s --prefix=/path/to/nowhere" % (configure, target)],
                    shell=True) != 0:
      self.error("Failed to configure")

    if target.startswith("nanomips"):
      if self.execute(command=["make", "-j", str(self.concurrency),
			       "all-binutils", "all-gas"]) != 0:
	self.error("Failed to build")
    else:
      if self.execute(command=["make", "-j", str(self.concurrency),
			       "all-binutils", "all-gas", "all-ld"]) != 0:
	self.error("Failed to build")

    self.execute(command=["make", "check-binutils"], env=env)
    self.registerLogFile(os.path.join(self.getWorkPath(), "binutils", "binutils.log"))
    log = os.path.join(self.getWorkPath(), "binutils", "binutils.sum")
    self.registerLogFile(log)
    self.parseLog(log)

    self.execute(command=["make", "check-gas"], env=env)
    self.registerLogFile(os.path.join(self.getWorkPath(), "gas", "testsuite", "gas.log"))
    log = os.path.join(self.getWorkPath(), "gas", "testsuite", "gas.sum")
    self.registerLogFile(log)
    self.parseLog(log)

    if not target.startswith("nanomips"):
      self.execute(command=["make", "check-ld"], env=env)
      self.registerLogFile(os.path.join(self.getWorkPath(), "ld", "ld.log"))
      log = os.path.join(self.getWorkPath(), "ld", "ld.sum")
      self.registerLogFile(log)
      self.parseLog(log)

    return self.success()

  def parseLog(self, log):
    fd = open(log)
    for l in fd.readlines():
      if l.startswith("ERROR: "):
        self.testsuiteSubmit(l[7:], False) 
      elif l.startswith("FAIL: "):
        self.testsuiteSubmit(l[6:], False) 
      elif l.startswith("XPASS: "):
        self.testsuiteSubmit(l[7:], False) 
      elif l.startswith("KPASS: "):
        self.testsuiteSubmit(l[7:], False) 
    fd.close()

