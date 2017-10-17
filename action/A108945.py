from Action import Action
import time
import os

# Step 1a

class A108945(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108945
    self.name = "Step 1a"

  # Execute the action.
  def run(self):
    time.sleep(2)
    host = self.getResource("Execution Host")
    example = self.getResource("Example Resource")
    result = (self.execute(command=["touch", "foo"]) == 0)
    self.execute(command=["touch", "share_file"], workdir=self.getSharedPath())
    self.registerLogFile(os.path.join(self.getSharedPath(), "share_file"))
    result = (self.execute(command=["cat"], spoofStdin="hello") == 0)
    self.success({"somefloat":0.4, "someint":34, "somestring":"wibble"})
    return result
