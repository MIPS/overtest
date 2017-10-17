import os
from common.Supertest2 import SuperTestAction
from Action import Action

# Build1

class A116464(SuperTestAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116464
    self.name = "Build1"

  def get_mode(self):
    return "compile"

  def get_testgroups(self):
    return []

