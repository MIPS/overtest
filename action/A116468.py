import os
from common.Supertest2 import SuperTestAction
from Action import Action

# Run1

class A116468(SuperTestAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116468
    self.name = "Run1"

  def get_mode(self):
    return "run"

  def get_testgroups(self):
    return []

