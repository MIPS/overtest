import os
from Action import Action

# Gcc2

class A109007(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 109007
    self.name = "Gcc2"

  # Execute the action.
  def run(self):
    return True
