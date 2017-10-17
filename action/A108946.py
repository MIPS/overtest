from Action import Action
import time

# Step 1b

class A108946(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108946
    self.name = "Step 1b"

  # Execute the action.
  def run(self):
    time.sleep(7)
    result = (self.execute(command=["cat", "/tmp/step1b"]) == 0)
    return result
