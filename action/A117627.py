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

# MeOS

class A117627(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117627
    self.name = "MeOS"

  # Execute the action.
  def run(self):
    workdir = self.getWorkPath()

    host = self.getResource ("Execution Host")
    da = self.getResource ("Debug Adapter")

    cvsroot = host.getAttributeValue ("LEEDS CVSROOT")

    METAG_INST_ROOT = self.config.getVariable ("METAG_INST_ROOT")

    version = self.version.split('.')
    meos_version = version[0:-1]
    meos_board   = version[-1]

    if not self.cvsCheckout(module="codescape/meos",
                            cvsroot=cvsroot,
                            tag="MEOS_%s_TAG" % '_'.join(meos_version)):
      atp120dp_ocm
      self.error("Failed to check out meos source")

    cmd = [ 'make',
            'BOARD=%s' % meos_board,
            'DA=%s' % da.getAttributeValue("DA Name"),
          ]

    env = {}
    env['METAG_INST_ROOT'] = METAG_INST_ROOT

    if self.execute(workdir=os.path.join(workdir, 'codescape', 'meos'),
                    command=cmd,
                    env=env) != 0:
      self.error("MeOS Tests failed")

    return self.success()
