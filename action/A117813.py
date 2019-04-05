from Action import Action

# GDB

class A117813(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117813
    self.name = "GDB"

  # Execute the action.
  def run(self):
    return self.gitFetch ("binutils-gdb.git")
