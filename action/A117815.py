from Action import Action

# Binutils

class A117815(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117815
    self.name = "Binutils"

  # Execute the action.
  def run(self):
    return self.gitFetch("binutils-gdb.git")
