from Action import Action

# SmallClib

class A117831(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117831
    self.name = "SmallClib"

  # Execute the action.
  def run(self):
    return self.gitFetch("smallclib.git")
