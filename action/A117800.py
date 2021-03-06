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
from Config import CONFIG
from Action import Action
from IMGAction import IMGAction
from OvertestExceptions import *

# Test Sim Examples

class A117800(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117800
    self.name = "Test Sim Examples"

  # Execute the action.
  def run(self):
    
    host = self.getResource("Execution Host")
    workDir = self.getWorkPath()
    cvsroot = host.getAttributeValue("KL metag CVSROOT")
    csimPath = self.config.getVariable("METAG_FSIM_ROOT")
    simTestVer = self.config.getVariable("Sim Tests Version")
    
    port = "4096"
    
    if csimPath == None:
       simVer = self.config.getVariable("Sim Version")
    else:
       simVer = "scratch"
    
    env = {}
    env['METAG_FSIM_ROOT'] = csimPath
    env['CVSROOT'] = cvsroot

    simTestNum = int(''.join(map(str,simTestVer.split('.'))))

    if simTestNum >= 10023:

      command = [ CONFIG.neo,
                 "sim/test_examples",
                 "FSIM=%s" % simVer,
                 "CONFIG=%s" % "garten",
                 "FSIM_ROOT=%s" % csimPath,
                 "SIMTEST_VER=%s" % simTestVer,
                 "PORT=%s" % port,
                 "TESTLOG_DIR=%s" % workDir]

    #Versions above 1.0.0.16 and below 1.0.0.23 include only the multisim example
    elif simTestNum > 10016:

          command = [ CONFIG.neo,
                 "sim/test_examples",
                 "-no-metac-sim",
                 "-no-sapdev",
                 "CONFIG=%s" % "frisa",
                 "FSIM=%s" % simVer,
                 "FSIM_ROOT=%s" % csimPath,
                 "SIMTEST_VER=%s" % simTestVer,
                 "PORT=%s" % port,
                 "TESTLOG_DIR=%s" % workDir]

    #Previous versions do not include any examples at all!
    else :
      self.warn("SIM TESTS FAILED - No examples included in this simTests version.")
      return self.failure()

    self.error("About to access KL metag CVS repository. Please fix action")
    result = self.execute(command=command, env=env)

    if result == 1:
      self.warn("SIM TESTS FAILED")
      return self.failure()
      logs = os.listdir(workDir)
      for f in logs:
          self.registerLogFile(f)

    else:
      if result > 1:
        self.warn("SIM TESTS return value = %d" % result)

      return self.success()
