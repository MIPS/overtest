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
from common.VerifySuiteParser import VerifySuiteParser
from common.KeyMaker import KeyMaker

# Verify CSIM

class A115231(Action, IMGAction, VerifySuiteParser, KeyMaker):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 115231
    self.name = "Verify CSIM"

  # Execute the action.
  def run(self):
    """
    Run the testsuite.
    If there is an execution task in this testrun the output from this
    testsuite is stored
    """
    verify = self.testrun.getVersion ("Verify")
    if verify != None and verify == "VHDL":
      # No CSIM build performed nor results submitted for VHDL tests
      return True

    toolkit_version = self.testrun.getVersion ("MetaMtxToolkit")
    PUB=None
    EXTRA=[]
    generateMD5 = self.config.getVariable("Generate MD5Sum?")

    if verify != None or generateMD5:
      PUB=os.path.join(self.getWorkPath())
      self.config.setVariable("Verify TGZs", PUB)

    # Convert the version into the pick and config variables
    board = self.config.getVariable('Target Board')
    core = board
    if " " in core:
      core = core.split()[0]

    if core == "COMET":
      pick="meta213_2t2d.csv"
      meta2_config="meta213_2t2d16"
    elif core == "214_4t2df":
      pick="meta2.csv"
      meta2_config="meta214_4t2df"
    elif core == "213_2t1d":
      pick="meta213_2t1d.csv"
      meta2_config="meta213_2t1d"
    elif core == "META122":
      cat = "meta1"
      target = "MC122"
    elif core == "MTX122":
      cat = "mtx"
      target = "MTXC122"
    else:
      pick="%s.csv" % core.lower()
      meta2_config=core.lower()

    if core in ("PEALLACH", "FRISA"):
      EXTRA.append("FPU=pvr")

    # Run the groups that were requested
    fpga_config = None
    groups = []
    if self.version == "static":
      if self.config.getVariable("Gold Tests?"):
        groups.append('gold')
      if self.config.getVariable("Grey Tests?"):
        groups.append('grey')
      if self.config.getVariable("Red Tests?"):
        groups.append('red')
      if self.config.getVariable("Azure Tests?"):
        groups.append('azure')
      if self.config.getVariable("Blue Tests?"):
        groups.append('blue')
      if self.config.getVariable("Purple Tests?"):
        groups.append('purple')
      subtargets="msub,chip"
      if core == "META122":
        subtargets+=",sdxx"
    elif self.version == "FPGA":
      if self.config.getVariable("Silver Tests?"):
        groups.append('silver')
      if self.config.getVariable("Steely Tests?"):
        groups.append('steely')
      if self.config.getVariable("Tarnish Tests?"):
        groups.append('tarnish')
      fpga_config = "tcf40"
      subtargets="fpga"
    else:
      self.error("Unknown version: %s" % self.version)
    
    res = 1
    summary = {}

    # Select whether MiniM is on or off
    MINIM=None
    if toolkit_version.startswith("2.3.3"):
      MINIM="NA"
    else:
      if not self.config.getVariable("MiniM Allowed?"):
        MINIM="OFF"
    
    # Select the correct python version
    python_ver = None
    if self.version == "static":
      python_ver = self.config.getVariable("Python Spec")

    if core in ["META122","MTX122"]:
      res = self.neoVerify ("publish", CAT=cat, TARGET=target,
                            SUBTARGETS=subtargets,
                            PYTHON=python_ver,
                            MATRIX=self.config.getVariable("Matrix ID"),
                            FPGA_CONFIG=fpga_config,
                            MINIM=MINIM,
                            PUB=PUB)
    else:
      # Build all the tests
      if len(groups) > 0:
        res = self.neoVerify ("select", CAT="meta2", TARGET="any",
                              PICK=pick,
                              GROUP=','.join(groups),
                              META2_CONFIG=meta2_config,
                              PYTHON=python_ver,
                              MATRIX=self.config.getVariable("Matrix ID"),
                              FPGA_CONFIG=fpga_config,
                              MINIM=MINIM,
                              EXTRA=EXTRA,
                              PUB=PUB)
      else:
        self.error("No groups enabled")

    if generateMD5:
      MD5KeysDictionary = self.getVerifyMD5Keys(PUB, self.version)
    else:
      MD5KeysDictionary = None


    summary = self.parseVerifyResults (self.fetchOutputFile (), MD5KeysDictionary)
    self.registerLogFile (os.path.join (self.getWorkPath (), ".publish.txt"))
    self.success(summary)
    return res == 0
