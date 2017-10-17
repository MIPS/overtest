import os
from Action import Action
from IMGAction import IMGAction
from common.KeyMaker import KeyMaker

# Verify

class A115232(Action, IMGAction, KeyMaker):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 115232
    self.name = "Verify"

  # Execute the action.
  def run(self):
    """
    Run the testsuite.
    Tests are taken from the TGZS directory
    """
    if self.version == "VHDL":
      return self.parseVHDLResults()

    type = self.testrun.getVersion("Verify CSIM")
    tests = self.config.getVariable("Verify TGZs")
    result = True
    verifykeys = self.getVerifyMD5Keys(tests, type)


    if self.version == "FPGA":
      verify_version = self.testrun.getVersion("VerifyToolkit")

      if type == "FPGA":
        result = self.neoRunall(VERIFY=verify_version,
                                PUB=tests,
                                script="fpga_runall",
                                keys=verifykeys)
      elif type == "static":
        result = self.neoRunall(VERIFY=verify_version,
                                PUB=tests,
                                script="python_runall",
                                keys=verifykeys)
    else:
      for test in verifykeys:
        self.testsuiteSubmit(test, True, version=verifykeys[test])

    return result

  def parseVHDLResults(self):
    """
    Parse the log files left behind after VHDL regression run
    """
    vhdl_resultdir = self.config.getVariable("VHDL Result Directory")
    # Whether to find and locate results for MiniM or Meta builds
    minim_results = (self.config.getVariable("MiniM Allowed?") == "Yes")

    # An example for submitting a test result, do this for all tests
    testname="a_test"
    testmd5sum="ABCDEF1234556579087"
    result=True # or False for failure
    status="PILOG"

    self.testsuiteSubmit(testname, result, version=testmd5sum, extendedresults={"Status":status})

    return True

