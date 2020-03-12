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
import re
from Action import Action
from common.VerificationSuite import VerificationSuiteAction

# CoreMark

class A117215(VerificationSuiteAction):
  def __init__(self, data):
    VerificationSuiteAction.__init__(self, data)
    self.actionid = 117215
    self.name = "CoreMark"

  def verify_template(self):
    return "ovt_%s" % self.version.split('.')[-1]

  def tests(self):
    if self.verify_template().split('_')[1] == "vhdl":
      return [ "cqdxmark1"  ]
    elif self.verify_template().split('_')[1] == "fpga":
      return [ "fcqdxmark1"  ]
    else:
      assert False

  def post_process(self):
    publish_txt = os.path.join(self.getWorkPath(), ".publish.txt")
    file = open(publish_txt)
    log = file.read()
    file.close()

    match = re.search("Thread 0: 'Ticks_S \d+', 'Ticks_E \d+', 'Ticks (\d+)', 'Active (\d+)', 'Idle (\d+)' and 'Speed (\d+)'", log)

    if match:
      ticks, active, idle, speed = match.group (1, 2, 3, 4)

      results = {'Timer Ticks'   : ticks,
                 'Active Cycles' : active,
                 'Idle Cycles'   : idle,
                 'Speed'         : speed,
                }

      return self.testsuiteSubmit(self.tests()[0], True, results)
    else:
      return self.error("Could not find CoreMark results")
