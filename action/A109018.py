import os
from Action import Action

# Secload

class A109018(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 109018
    self.name = "Secload"

  # Execute the action.
  def run(self):
    return True
