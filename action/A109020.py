import os
from Action import Action

# Gcc2Libstdc++Testsuite

class A109020(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 109020
    self.name = "Gcc2Libstdc++Testsuite"

  # Execute the action.
  def run(self):
    return True
