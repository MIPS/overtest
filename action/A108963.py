import os
from common.Supertest import A_supertest_generic

# Build mecc supertest (Slow Tests)

class A108963(A_supertest_generic):
  def get_config_mode(self):
    return 'compile'

  def get_config_configs(self):
    return []

  def get_config_testgrps(self):
    return ['Ydepth-opmix']

  def __init__(self, data):
    A_supertest_generic.__init__(self, data)
    self.actionid = 108963
    self.name = "Build mecc supertest (Slow Tests)"
