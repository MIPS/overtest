import os
from Action import Action

# Python

class A117845(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117845
    self.name = "Python"

  # Execute the action.
  def run(self):
    return self.gitFetch ("cpython.git")
