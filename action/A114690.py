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
import glob
from utils.Utilities import versionCompare
from Action import Action
from IMGAction import IMGAction
from Config import CONFIG

# BuildMECCToolkit

class A114690(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 114690
    self.name = "BuildMECCToolkit"

  # Execute the action.
  def run(self):
    host = self.getResource('Execution Host')
    p4port = str(host.getAttributeValue('P4PORT'))

    workdir = self.config.getVariable ("MECC_RELEASE_ROOT")
    metag_inst_root = self.config.getVariable ("METAG_INST_ROOT")

    COBIT_INST_ROOT = self.config.getVariable("COBIT_INST_ROOT")

    cmp_ver = self.testrun.getVersion ("BuildMECCToolkit")

    license_file = os.path.join(os.path.expanduser("~"), "licenses")

    env = {'P4PORT' : p4port,
           'P4USER' : 'xbuild.meta',
          }
    env['PATH'] = CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo),
                                         os.path.join(COBIT_INST_ROOT, 'bin'),
                                         os.environ['PATH']])
    cmd = [ './scripts/all.sh', '--TOOLKIT_VERSION', cmp_ver, 
                                '--METAG_INST_ROOT', metag_inst_root, 
                                '--LICENSE_FILE', license_file]
    
    if bool(self.config.getVariable("MECC_BOOTSTRAP")):
      cmd.append('--BOOTSTRAP')

    if not self.config.getVariable ("MECC_DO_WINDOWS"):
      cmd.extend (["--SKIP_WINDOWS"])

    mingw_root = self.config.getVariable ("GCCMINGW_ROOT")
    cmd.extend(['--MINGW', mingw_root])

    env['EXTRA_PATH'] = CONFIG.makeSearchPath([])

    result = self.execute(env=env, command=cmd, workdir="%s/mecc/release"%workdir)
    if result != 0:
      self.error ("Could not build MECC")

    return self.success ()
