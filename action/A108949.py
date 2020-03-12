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

# Build metag toolkit

class A108949(Action):
  dir_force_32_bit    = os.path.join ('metag', 'tools', 'gcc2testing', 'build', 'force32bit')
  file_tscript        = os.path.join ('metag', 'tools', 'scripts', 'tscript');
  file_gcc            = os.path.join ('metag-local', 'bin', 'gcc')

  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108949
    self.name = "Build metag toolkit"

  # Execute the action.
  def run(self):
    env = {}

    # Get all the directories involved
    work_dir              = self.getWorkPath()
    dir_metag_source      = self.config.getVariable("METAG_SOURCE_ROOT")
    dir_metag_scripts     = os.path.join (dir_metag_source, "metag", "tools", "scripts")
    dir_force_32_bit      = os.path.join (dir_metag_source, self.dir_force_32_bit)
    file_gcc              = os.path.join (work_dir, self.file_gcc)

    # Output the new variables
    self.config.setVariable("METAG_INST_ROOT", work_dir)

    if self.debug_verbose:
      print "Inputs:"
      print "\tToolkit source:   %s" % (dir_metag_source)
      print "Working:"
      print "\tWork dir:         %s" % (work_dir)
      print "\t32 bit gcc et al: %s" % (dir_force_32_bit)

    self.logHelper ("Starting METAG Toolkit Build")
    if self.testrun.debug_allow_skipping and os.path.exists (file_gcc):
      self.testrun.skip ("Building toolkit")
    else:
      env['METAG_INST_ROOT'] = work_dir
      env['PATH'] = "%s:%s" % (dir_force_32_bit,os.environ['PATH'])
      result = self.execute(env=env, workdir=dir_metag_scripts, command=["./gcc_toolkit"])
      if not result == 0:
        self.error("Couldn't build toolkit")
    return self.success ()
