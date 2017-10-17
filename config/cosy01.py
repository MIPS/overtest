"""
Module for cosy01 config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Config for cosy01
  """
  fqdn = "cosy01.kl.imgtec.org"
  localdir = "/user/cosytemp/overtest/root/"
  logdir = "/user/cosytemp/overtest/root/"
  shareddir = "/user/cosytemp/overtest/root/"
