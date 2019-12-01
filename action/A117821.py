from Action import Action

# QEMU

class A117821(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117821
    self.name = "QEMU"

  # Execute the action.
  # Qemu source archives must be created by executing
  # scripts/archive-source.sh within the qemu source tree which needs
  # a deep check-out to work correctly.
  def run(self):
    return self.gitFetch("gnutools-qemu.git", deep=True)
