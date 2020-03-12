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

# Build GCC 4 based test toolkit

class A108967(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108967
    self.name = "Build GCC 4 based test toolkit"

  # Execute the action.
  def run(self):
    # Find where the source was checked out to
    source = self.config.getVariable("METAG_SOURCE_ROOT")
    METAG_INST_ROOT = self.config.getVariable("METAG_INST_ROOT")
    if METAG_INST_ROOT == "":
      METAG_INST_ROOT=self.getWorkPath()
      self.config.setVariable("METAG_INST_ROOT", METAG_INST_ROOT)

    self.config.setVariable("GCC build path", os.path.join(source, "target", "gcc2"))

    # Construct the path to the build directory
    dir_build = os.path.join(source, "metag", "tools", "gcc2testing", "build")

    # Specify the current work directory as the destination
    env = {"METAG_INST_ROOT":METAG_INST_ROOT}

    # Build the toolkit (this will modify the working area from the source fetch
    # stage! 
    result = self.execute(command=["make", "-j4", "install"], env=env, workdir=dir_build)

    if result == 0:
      return self.success()
    else:
      self.error("Build failed")
