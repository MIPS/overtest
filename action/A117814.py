from Action import Action

# Newlib

class A117814(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117814
    self.name = "Newlib"

  # Execute the action.
  def run(self):
    return self.gitFetch("newlib.git")
