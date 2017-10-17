import os
from Action import Action

# BinUtilsLocal

class A109006(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 109006
    self.name = "BinUtilsLocal"

  # Execute the action.
  def run(self):
    return True
