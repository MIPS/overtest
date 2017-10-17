import os
from common.Supertest2 import SuperTestAction
from Action import Action

# Run2

class A116469(SuperTestAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116469
    self.name = "Run2"

  def get_mode(self):
    return "run"

  def get_testgroups(self):
    return []

