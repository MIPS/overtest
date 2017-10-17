import os
from Action import Action

# VerifyToolkit

class A108999(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108999
    self.name = "VerifyToolkit"

  # Execute the action.
  def run(self):
    return True
