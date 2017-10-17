import os
from common.Supertest2 import SuperTestAction
from Action import Action

# BuildInitial

class A116457(SuperTestAction):
  def __init__(self, data):
    SuperTestAction.__init__(self, data)
    self.actionid = 116457
    self.name = "BuildInitial"

  def get_mode(self):
    return "compile"

  def get_testgroups(self):
    return ["EmbeddedC"]

