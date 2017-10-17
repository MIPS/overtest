import os
from Action import Action

# MetaMtxCoreSimStub

class A113860(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 113860
    self.name = "MetaMtxCoreSimStub"

  # Execute the action.
  def run(self):
    return True
