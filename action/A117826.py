from Action import Action

# uClibc

class A117826(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117826
    self.name = "uClibc"

  # Execute the action.
  def run(self):
    return self.gitFetch("uclibc.git")
