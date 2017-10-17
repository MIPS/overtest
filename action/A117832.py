import os
from Action import Action

# EEMBC 1.1

class A117832(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117832
    self.name = "EEMBC 1.1"

  # Execute the action.
  def run(self):
    self.error("NOT IMPLEMENTED")
