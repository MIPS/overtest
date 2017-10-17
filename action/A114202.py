import os
from Action import Action
from IMGAction import IMGAction

# vhdl_stork FPGA

class A114202(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 114202
    self.name = "vhdl_stork FPGA"

  # Execute the action.
  def run(self):
    """
    Run the testsuite.
    Tests are taken from the TGZS directory
    """
    return self.neoRunall(VERIFY=self.testrun.getVersion("VerifyToolkit"),
                          PUB=self.config.getVariable("VERIFY_VHDL_STORK_TGZS"),
                          script="python_runall")
