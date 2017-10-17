import os
from Action import Action

# Gcc2CompilerTestsuite

class A109019(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 109019
    self.name = "Gcc2CompilerTestsuite"

  # Execute the action.
  def run(self):
    return True
