from Action import Action

# Dejagnu

class A117816(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117816
    self.name = "Dejagnu"

  # Execute the action.
  def run(self):
    return self.gitFetch("dejagnu.git")
