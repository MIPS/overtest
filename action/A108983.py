import os
from Action import Action

# Embedded Assembler

class A108983(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108983
    self.name = "Embedded Assembler"

  # Execute the action.
  def run(self):
    # Fetch the installation folder
    METAG_INST_ROOT = self.config.getVariable("METAG_INST_ROOT")

    if METAG_INST_ROOT == "":
      METAG_INST_ROOT = self.getWorkPath()
      self.config.setVariable("METAG_INST_ROOT", METAG_INST_ROOT)

    host = self.getResource("Execution Host")
    binary_dir = host.getAttributeValue("Binary Release Dir")
    assembler = os.path.join(binary_dir, "as", "%s.tgz"%self.version)

    # Execute an arbitrary command overriding some environment variables
    result = self.execute(command=["tar", "-xzf", assembler], workdir=METAG_INST_ROOT)

    return (result == 0)
