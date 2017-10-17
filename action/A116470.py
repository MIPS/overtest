import os
from common.Supertest2 import SuperTestAction
from Action import Action

# RunOpmix

class A116470(SuperTestAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116470
    self.name = "RunOpmix"

  def get_mode(self):
    return "run"

  def get_testgroups(self):
    return ["Ydepth-opmix"]

