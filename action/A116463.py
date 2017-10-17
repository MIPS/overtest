import os
from common.Supertest2 import SuperTestAction
from Action import Action

# RunInitial

class A116463(SuperTestAction):
  def __init__(self, data):
    SuperTestAction.__init__(self, data)
    self.actionid = 116463
    self.name = "RunInitial"

  def get_mode(self):
    return "run"

  def get_testgroups(self):
    return ["EmbeddedC"]

