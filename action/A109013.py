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

# Example Testsuite

class A109013(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 109013
    self.name = "Example Testsuite"

  # Execute the action.
  def run(self):
    self.testsuiteSubmit("My First Test", True, {"stringres":"fred", "intres":1, "floatres":1.1, "boolres":False})
    self.testsuiteSubmit("My Second Test", True, {"stringres":"fred2", "intres":2, "floatres":2.2, "boolres":True}, "1.1")
    self.success({"mystr":"bar", "myint":10, "myfloat":3.5, "mybool":True})
    return True
