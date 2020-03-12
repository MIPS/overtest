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
from action.Action import Action

# Build mecc supertest (a)

class A_supertest_generic(Action):
  def get_config_mode(self):
    assert 0

  def get_config_configs(self):
    assert 0

  def get_config_testgrps(self):
    assert 0

  def __init__(self, data):
    Action.__init__(self, data)

  # Execute the action.
  def run(self):
    work_dir = self.getWorkPath()

    metag_inst_root = self.config.getVariable ('METAG_INST_ROOT')
    metag_fsim_root = self.config.getVariable ('METAG_FSIM_ROOT')
    mecc_inst_root  = self.config.getVariable ('MECC_INST_ROOT')
    supertest_inst_root = self.config.getVariable ('SUPERTEST_INST_ROOT')

    if self.debug_verbose:
      print "Inputs:"
      print "\tMECC_INST_ROOT:%s" % (mecc_inst_root)
      print "\tMETAG_INST_ROOT:%s" % (metag_inst_root)
      print "\tMETAG_FSIM_ROOT:%s" % (metag_fsim_root)
      print "\tSupertest dir: %s" % (supertest_inst_root)
      print "Working:"
      print "\tWork dir:      %s" % (work_dir)

    # WORK NEEDED: deprecate FSIM_INST_ROOT
    spoofStdin = ['export CORE=2.1',
                  'export ALLOW_REMOTE_HASP=1',
                  'export MECC_INST_ROOT="%s"'  % mecc_inst_root,
                  'export LM_LICENSE_FILE="%s"'  % os.path.join(os.path.expanduser("~"), "licenses", "uncounted.lic"),
                  'export METAG_INST_ROOT="%s"' % metag_inst_root,
                  'export METAG_FSIM_ROOT="%s"' % metag_fsim_root,
                  'export FSIM_INST_ROOT="%s"'  % metag_fsim_root,
                  'export MECC="$MECC_INST_ROOT/metag-local/bin/mecc"',
                  'chmod u+x do-tests/%s-all.pl' % self.get_config_mode(),
                  'chmod u+x do-tests/takejob.pl',
                  ('do-tests/%s-all.pl --serverhost=cosy01 %s %s'
                       % (self.get_config_mode(),
                          ' '.join (['--config='  + x for x in self.get_config_configs()]),
                          ' '.join (['--testgrp=' + x for x in self.get_config_testgrps()]))),
                 ]
    spoofStdin = ''.join ([x + '\n' for x in spoofStdin])

    result = self.execute(command=["product", "enter"], spoofStdin=spoofStdin, workdir=supertest_inst_root)
    if not result == 0:
      self.error("Build supertest")

    return self.success ()
