from Action import Action
from IMGAction import IMGAction

# vhdl_213_2t1d FPGA

class A114205(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 114205
    self.name = "vhdl_213_2t1d FPGA"

  # Execute the action.
  def run(self):
    """
    Run the testsuite.
    Tests are taken from the TGZS directory
    """
    return self.neoRunall(VERIFY=self.testrun.getVersion("VerifyToolkit"),
                          PUB=self.config.getVariable("VERIFY_VHDL_213_2T1D_TGZS"),
                          script="python_runall")
