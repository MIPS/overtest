import os
from Action import Action

# Embedded Link Loader

class A108985(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108985
    self.name = "Embedded Link Loader"

  # Execute the action.
  def run(self):
    # Fetch the installation folder
    METAG_INST_ROOT = self.config.getVariable("METAG_INST_ROOT")

    host = self.getResource("Execution Host")
    binary_dir = host.getAttributeValue("Binary Release Dir")
    ldlk = os.path.join(binary_dir, "ldlk", "%s.tgz"%self.version)

    # Execute an arbitrary command overriding some environment variables
    result = self.execute(command=["tar", "-xzf", ldlk], workdir=METAG_INST_ROOT)

    return (result == 0)

