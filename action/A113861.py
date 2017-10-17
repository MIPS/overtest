from Action import Action
from IMGAction import IMGAction

# vhdl_heron FPGA

class A113861(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 113861
    self.name = "vhdl_heron FPGA"

  # Execute the action.
  def run(self):
    """
    Run the testsuite.
    Tests are taken from the TGZS directory
    """
    return self.neoRunall(VERIFY=self.testrun.getVersion("VerifyToolkit"),
                          PUB=self.config.getVariable("VERIFY_VHDL_HERON_TGZS"),
                          script="python_runall")

