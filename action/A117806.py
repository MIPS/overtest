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

# Verify SIMINFO

class A117806(Action, IMGAction, VerifySuiteParser, KeyMaker):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117806
    self.name = "Verify SIMINFO"

  #Variables common to all tests
  MINIM = "OFF"
  group = "gold"
  subtargets = "msub,chip,sdxx"

  #Function to run a test with neo verify
  def runTest(self, test_name, core, PUB, EXTRA=None):

    pick="%s.csv" % core.lower()
    meta2_config=core.lower()
    python_ver = self.config.getVariable("Python Spec")

    res = self.neoVerify ("select", CAT="meta2", TARGET="any",
                           GROUP=self.group,
                           SUBTARGETS=self.subtargets,
                           PICK=pick,
                           META2_CONFIG=meta2_config,
                           PYTHON=python_ver,
                           MATRIX=self.config.getVariable("Matrix ID"),
                           MINIM=self.MINIM,
                           EXTRA=EXTRA,
                           JUSTONE=test_name,
                           PUB=PUB)
    return res

  #Execute the action.
  def run(self):
    
    verify = self.testrun.getVersion ("Verify")
    toolkit_version = self.testrun.getVersion ("MetaMtxToolkit")

    EXTRA=[]
    Results=[]

    #Open files for logging the combined results for all tests.
    f_log = open(os.path.join(self.getWorkPath(), 'all_test.txt'), 'w+')
    f_plog = open(os.path.join(self.getWorkPath(), 'all_publish.txt'), 'w+')

    #Arrays of selected tests to run on every core.
    tests_garten=["dtest", "qmmark1"]
    tests_frisa=["dsptest10", "dsptest11", "dsptest30"]

    MD5KeysDictionary = {}
    summary = {}

    #Test Dhrystone and qmmark1 on Garten first
    core = "GARTEN"

    #Execute all tests in tests_garten
    for test in tests_garten:
      test_name = test
      PUB=os.path.join(self.getWorkPath(), test_name)
      #Run the test
      Results.append(self.runTest(test_name, "%s"%core, PUB))

      #Get the md5 key from this test results
      MD5KeysDictionary.update(self.getVerifyMD5Keys(PUB, "static", info_on=1))

      #Append output to big log file
      fr = open(self.fetchOutputFile(), 'r')
      f_log.write(fr.read())

      #Append the contents of publish.txt for this file to all_publish.txt
      fr.close()
      fr = open(os.path.join(self.getWorkPath(), '.publish.txt'), 'r')
      f_plog.write(fr.read())

    #Test some dsptests on Frisa next
    core = "FRISA"
    EXTRA.append("FPU=pvr")

    #Execute all tests in tests_frisa
    for test in tests_frisa:
      test_name = test
      PUB=os.path.join(self.getWorkPath(), "%s" %test_name)
      Results.append(self.runTest(test_name, "%s"%core, PUB, EXTRA))

      #Get the md5 key from this test results
      MD5KeysDictionary.update(self.getVerifyMD5Keys(PUB, "static", info_on=1))

      #append output to big log file
      fr = open(self.fetchOutputFile(), 'r')
      f_log.write(fr.read())

      #append the contents of publish.txt for this file to big all_publish.txt
      fr.close()
      fr = open(os.path.join(self.getWorkPath(), '.publish.txt'), 'r')
      f_plog.write(fr.read())

    f_log.close()
    f_plog.close()

    #File to hold tests summary
    f_log_fin = open(os.path.join(self.getWorkPath(), 'final_log.txt'), 'w+')

    #Get script to combine results in a summary and put it in final_log.txt
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue ("KL metag CVSROOT")

    self.error("About to access KL metag CVS repository, please fix action")
    module = os.path.join('metag', 'verify', 'metac', 'meta2', 'publish_rpt.awk')
    self.cvsCheckout(module, cvsroot)

    log_path = os.path.join(self.getWorkPath(), "all_publish.txt")

    self.execute (command=["%s"%module, "%s"%log_path ], silent=False)

    fr = open(self.fetchOutputFile(), 'r')
    f_log_fin.write(fr.read())

    self.execute (command=["rm", "-rf", "metag"])

    f_log_fin.close()
    fr.close()

    #Summarize results
    summary = (self.parseVerifyResults ( os.path.join(self.getWorkPath(),'final_log.txt'), MD5KeysDictionary))

    self.registerLogFile (os.path.join (self.getWorkPath (), "final_log.txt"))
    self.registerLogFile (os.path.join (self.getWorkPath (), "all_test.txt"))
    self.registerLogFile (os.path.join (self.getWorkPath (), "all_publish.txt"))

    self.success(summary)

    if True in Results:
      return False
    else:
      return True
