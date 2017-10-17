import os
from Action import Action

# BootloaderToolkitStub

class A117773(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117773
    self.name = "BootloaderToolkitStub"

  # Execute the action.
  def run(self):
    return True
