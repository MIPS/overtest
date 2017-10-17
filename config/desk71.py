"""
Module for desk71 config
"""
import config.centos45

class Config(config.centos45.Config):
  """
  Class for desk71 config
  """
  fqdn = "desk71.kl.imgtec.org"
  localdir = "/tmp/overtest/root/"
  logdir = "/tmp/overtest/root/"
  shareddir = "/tmp/overtest/shared/"
