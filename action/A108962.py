import os
from common.Supertest import A_supertest_generic

# Build mecc supertest (a)

class A108962(A_supertest_generic):
  def get_config_mode(self):
    return 'compile'

  def get_config_configs(self):
    return ['EmbeddedC']

  def get_config_testgrps(self):
    return ['EmbeddedCIMG']

  def __init__(self, data):
    A_supertest_generic.__init__(self, data)
    self.actionid = 108962
    self.name = "Build mecc supertest (a)"
