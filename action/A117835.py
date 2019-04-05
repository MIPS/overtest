from Action import Action

# Musl

class A117835(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117835
    self.name = "Musl"

  # Execute the action.
  def run(self):
    return self.gitFetch("musl.git")
