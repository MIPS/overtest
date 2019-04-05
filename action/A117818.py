from Action import Action

# Glibc

class A117818(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117818
    self.name = "Glibc"

  # Execute the action.
  def run(self):
    return self.gitFetch("glibc.git")
