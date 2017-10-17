import os
from Action import Action

# VerifyToolkitStub

class A117790(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117790
    self.name = "VerifyToolkitStub"

  # Execute the action.
  def run(self):
    return True
