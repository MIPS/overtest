import os
from Action import Action

# Embedded Linker

class A108984(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108984
    self.name = "Embedded Linker"

  # Execute the action.
  def run(self):
    # Fetch the installation folder
    METAG_INST_ROOT = self.config.getVariable("METAG_INST_ROOT")

    host = self.getResource("Execution Host")
    binary_dir = host.getAttributeValue("Binary Release Dir")
    linker = os.path.join(binary_dir, "ld", "%s.tgz"%self.version)

    # Execute an arbitrary command overriding some environment variables
    result = self.execute(command=["tar", "-xzf", linker], workdir=METAG_INST_ROOT)

    return (result == 0)

