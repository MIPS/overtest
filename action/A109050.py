import os
from Action import Action

# Gcc

class A109050(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 109050
    self.name = "Gcc"

  # Execute the action.
  def run(self):
    return True
