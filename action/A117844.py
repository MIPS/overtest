import os
from Action import Action

# GDB-Py

class A117844(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117844
    self.name = "GDB-Py"

  # Execute the action.
  def run(self):
    return self.gitFetch ("binutils-gdb.git")
