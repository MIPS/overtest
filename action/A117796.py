import os
from Action import Action

# Bullet Source

class A117796(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117796
    self.name = "Bullet Source"

  # Execute the action.
  def run(self):
    return True
