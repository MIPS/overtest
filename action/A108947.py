from Action import Action

# Step 2

class A108947(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108947
    self.name = "Step 2"

  # Execute the action.
  def run(self):
    if self.actionid != 108947:
      self.error("INTERNAL ERROR: Action ID set incorrectly: %s" % self.actionid)
    if self.name != "Step 2":
      self.error("INTERNAL ERROR: Name set incorrectly: %s" % self.name)

    result = (self.execute(command=["cat", "/tmp/step2"]) == 0)
    return result
