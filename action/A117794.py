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

# Comet DAB Radio

class A117794(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117794
    self.name = "Comet DAB Radio"

  # Execute the action.
  def run(self):
    METAG_INST_ROOT=self.config.getVariable("METAG_INST_ROOT")
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("KL metag CVSROOT")

    if self.config.getVariable("Tuner") == "Mirics MSI002":
      if self.config.getVariable("Mirics Tuner Mod") == "na":
        self.error("Mirics Tuner Mod must be set explicitly")
    if self.config.getVariable("Tuner") == "Maxim MAX2172":
      if self.config.getVariable("Mirics Tuner Mod") != "na":
        self.error("Mirics Tuner Mod must be set to Not Applicable for MAXIM tuner")

    toolkit_version = self.testrun.getVersion("MetaMtxToolkitStub")
    tk_parts = toolkit_version.split(".")
    COMET_API_TK="2.7"
    if len(tk_parts) >= 2:
      tk_major="%s.%s"% (tk_parts[0], tk_parts[1])
      if tk_major in ("2.5", "2.6", "2.7"):
        COMET_API_TK=tk_major

    env={}
    env['METAG_INST_ROOT'] = METAG_INST_ROOT
    env['COMET_API_TK'] = COMET_API_TK
    target_type=self.config.getVariable("Target Board")
    if target_type == "COMET Metamorph":
      env['BOARD'] = "COMETMETAMORPHWITHMIRICSTUNER"
    elif target_type == "PEGASUS":
      env['BOARD'] = "PEGASUS"
    else:
      self.error("Unsupported Target Board: %s" % target_type)

    if not self.cvsCheckout("metag/tools/gcc2testing/cometdabradio", cvsroot):
      self.error("Unable to check out cometdabradio")

    result = self.execute(command=[os.path.join("metag", "tools", "gcc2testing",
                                                "cometdabradio", "v%s.sh" % self.version)],
                          shell=True,
                          env=env)

    if result != 0:
      self.error("Failed to build comet dab radio package")

    self.registerLogFile(os.path.join(self.getWorkPath(), "test_METAGCC.tgz"))
    self.registerLogFile(os.path.join(self.getWorkPath(), "dab_MTXGCC.tgz"))
    self.registerLogFile(os.path.join(self.getWorkPath(), "scripts.tgz"))
    self.registerLogFile(os.path.join(self.getWorkPath(), "COMET_DAB_RADIO_V_1_4_0", "RUNME.txt"))

    return True
