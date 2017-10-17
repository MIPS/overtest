"""
Module for fwbuild-linux config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Class for fwbuild-linux config
  """
  fqdn = "fwbuild-linux.le.imgtec.org"
  localdir = "/home/overtest/root/"
  logdir = "/home/overtest/root/"
  shareddir = "/share/meta/shared/overtest/"
