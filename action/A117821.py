from Action import Action

# QEMU

class A117821(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117821
    self.name = "QEMU"

  # Execute the action.
  def run(self):
    return self.gitFetch("qemu.git")
