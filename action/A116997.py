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

# AXD Firmware Build

class A116997(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116997
    self.name = "AXD Firmware Build"

  # Execute the action.
  def run(self):
    METAG_INST_ROOT = self.config.getVariable("METAG_INST_ROOT")

    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("LEEDS CVSROOT")

    # Check out AXD
    result = self.cvsCheckout("axd-firmware", cvsroot=cvsroot)

    if not result:
      self.error("Failed to check out AXD firmware")

    scriptdir = os.path.join(self.getWorkPath(), "axd-firmware")

    env={'FORCE_METAG_INST_ROOT' : METAG_INST_ROOT}

    for script in ["build_mp3", "build_aac"]:
      result = self.execute(command=[os.path.join(".",script)], shell=True, workdir=scriptdir, env=env)

      if result != 0:
        self.error("Failed to build: %s" % script)

    self.config.setVariable('AXD_FIRMWARE_OUTPUT', os.path.join(self.getWorkPath(), "axd-firmware"))

    return True
