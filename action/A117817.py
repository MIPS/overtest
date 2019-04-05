from Action import Action

# Packages

class A117817(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117817
    self.name = "Packages"

  # Execute the action.
  def run(self):
    return self.gitFetch("packages.git")
