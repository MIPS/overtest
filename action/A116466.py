import os
from common.Supertest2 import SuperTestAction
from Action import Action

# BuildOpmix

class A116466(SuperTestAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116466
    self.name = "BuildOpmix"

  def get_mode(self):
    return "compile"

  def get_testgroups(self):
    return ["Ydepth-opmix"]

