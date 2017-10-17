"""
Module for cosy03 config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Class for cosy03 config
  """
  fqdn = "cosy03.kl.imgtec.org"
  localdir = "/user/cosytemp/overtest/root/"
  logdir = "/user/cosytemp/overtest/root/"
  shareddir = "/user/cosytemp/overtest/root/"
