import os
from common.Supertest2 import SuperTestAction
from Action import Action

# Build2

class A116465(SuperTestAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116465
    self.name = "Build2"

  def get_mode(self):
    return "compile"

  def get_testgroups(self):
    return []

