from Action import Action
from IMGAction import IMGAction

# vhdl_214_4t2df FPGA

class A114204(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 114204
    self.name = "vhdl_214_4t2df FPGA"

  # Execute the action.
  def run(self):
    """
    Run the testsuite.
    Tests are taken from the TGZS directory
    """
    return self.neoRunall(VERIFY=self.testrun.getVersion("VerifyToolkit"),
                          PUB=self.config.getVariable("VERIFY_VHDL_214_4T2DF_TGZS"),
                          script="python_runall")
