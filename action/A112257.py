import os
from Action import Action

# Linux testing SYNC

class A112257(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 112257
    self.name = "Linux testing SYNC"

  # Execute the action.
  def run(self):
    return True
