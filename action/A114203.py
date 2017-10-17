from Action import Action
from IMGAction import IMGAction

# vhdl_kfish FPGA

class A114203(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 114203
    self.name = "vhdl_kfish FPGA"

  # Execute the action.
  def run(self):
    """
    Run the testsuite.
    Tests are taken from the TGZS directory
    """
    return self.neoRunall(VERIFY=self.testrun.getVersion("VerifyToolkit"),
                          PUB=self.config.getVariable("VERIFY_VHDL_KFISH_TGZS"),
                          script="python_runall")
