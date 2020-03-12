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
from Action import Action
import time
import os

# Step 1a

class A108945(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108945
    self.name = "Step 1a"

  # Execute the action.
  def run(self):
    time.sleep(2)
    host = self.getResource("Execution Host")
    example = self.getResource("Example Resource")
    result = (self.execute(command=["touch", "foo"]) == 0)
    self.execute(command=["touch", "share_file"], workdir=self.getSharedPath())
    self.registerLogFile(os.path.join(self.getSharedPath(), "share_file"))
    result = (self.execute(command=["cat"], spoofStdin="hello") == 0)
    self.success({"somefloat":0.4, "someint":34, "somestring":"wibble"})
    return result
