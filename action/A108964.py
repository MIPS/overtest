import os
from common.Supertest import A_supertest_generic

# Run mecc supertest (a)

class A108964(A_supertest_generic):
  def get_config_mode(self):
    return 'run'

  def get_config_configs(self):
    return []

  def get_config_testgrps(self):
    return []

  def __init__(self, data):
    A_supertest_generic.__init__(self, data)
    self.actionid = 108964
    self.name = "Run mecc supertest (a)"
