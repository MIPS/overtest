"""
Module for skiddaw config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Class for skiddaw config
  """
  fqdn = "skiddaw.le.imgtec.org"
  localdir = "/home/overtest/root/"
  logdir = "/home/overtest/root/"
  shareddir = "/share/meta/shared/overtest/"
