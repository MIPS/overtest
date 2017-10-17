import os
from Action import Action

# META Linux Bootloader

class A115225(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 115225
    self.name = "META Linux Bootloader"

  # Execute the action.
  def run(self):
    return True
