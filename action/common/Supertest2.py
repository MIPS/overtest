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
from Config import CONFIG

class SuperTestAction(Action):
  def __init__(self, data):
    Action.__init__(self, data)

  def get_mode(self):
    assert False

  def get_testgroups(self):
    return []

  def get_testgroupopts(self):
    return [ "--testgrp=%s" % x for x in self.get_testgroups() ]

  # Execute the action.
  def run(self):
    dir_cadese = os.path.join ('/user', 'local_cosy')
    serverhost = self.getResource("Execution Host").getHostName()

    workdir = os.path.join (self.config.getVariable ("ST_SOURCE_ROOT"), "supertest")
    spoofStdin = [[],
                  [ "export", "MECC_INST_ROOT='%s'" % self.config.getVariable("MECC_INST_ROOT") ],
                  [ "export", "LM_LICENSE_FILE='%s'" % os.path.join(os.path.expanduser("~"), "licenses", "uncounted.lic")],
                  [ "export", "METAG_INST_ROOT='%s'" % self.config.getVariable("METAG_INST_ROOT") ],
                  [ "export", "METAG_FSIM_ROOT='%s'" % self.config.getVariable("METAG_FSIM_ROOT") ],
                  [ "export", "PATH=%s" % CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo),
                                                                 "$PATH"])],
                  [ "export", "ALLOW_REMOTE_HASP=1" ],
                  [ "./do-tests/%s-all.pl" % self.get_mode(),
                    "--results=$PWD/results",
                    "--serverhost=%s" % serverhost,
                  ] + self.get_testgroupopts(),
                  [ "exit" ]
                 ]
    spoofStdin = [ ' '.join(x) for x in spoofStdin ]
    spoofStdin = '\n'.join(spoofStdin)

    print "BEGIN STDIN"
    print spoofStdin
    print "END STDIN"

    cmd = [ "product", "enter" ]

    env = { 'PATH': CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo),
                                           '%s/product/bin:%s/cadese/bin:%s/sccs/bin' % (dir_cadese,
                                                                                         dir_cadese,
                                                                                         dir_cadese),
                                           os.environ['PATH']])
          }
    result = self.execute(env=env, command=cmd, workdir=workdir, spoofStdin=spoofStdin)

    if not result == 0:
      self.error ("Failed to run command")

    return self.success ()
