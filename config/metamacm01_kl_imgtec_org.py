"""
Module for metamacm01 config
"""
import config.darwin

class Config(config.darwin.Config):
  """
  Class for metamacm01 config
  """
  fqdn = "metamacm01.kl.imgtec.org"
  localdir = "/user/metatemp/overtest/root/"
  logdir = "/user/metatemp/overtest/root/"
  shareddir = "/user/metatemp/overtest/root/"
