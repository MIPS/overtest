"""
Module for Matthew Fortune's desktop config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Config for Matthew Fortune's Desktop (CentOS 5 but compatible with 4.5 config)
  """
  fqdn = "mfortune-linux.le.imgtec.org"
  localdir = "/home/overtest/root/"
  logdir = "/home/overtest/root/"
  shareddir = "/share/meta/shared/overtest/"
