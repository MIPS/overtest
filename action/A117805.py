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
from Perforce import PerforceConnection

# Fetch

class A117805(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117805
    self.name = "Fetch"

  # Execute the action.
  def run(self):
    host = self.getResource('Execution Host')
    p4port = str(host.getAttributeValue('P4PORT'))

    changelist = int(self.config.getVariable('LLVM_P4_CHANGELIST'))
    workspace_template = 'MAIN_LLVM_WS'

    root = self.getWorkPath ()

    conn = PerforceConnection(p4user='xbuild.meta', p4port=p4port)

    clientdef = conn.make_temporary_client_def(workspace_template, root=root)

    with clientdef as client:
      client.sync('@%d' % changelist)

    self.config.setVariable('LLVM_AUTO_SRC_DIR', root)

    return True
