from Action import Action

# GOLD

class A117834(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117834
    self.name = "GOLD"

  # Execute the action.
  def run(self):
    return self.gitFetch("binutils-gdb.git")
