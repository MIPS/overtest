"""
Module for klmeta06 config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Class for klmeta06 config
  """
  fqdn = "klmeta06.kl.imgtec.org"
  localdir = "/user/metatemp/overtest/root/"
  logdir = "/user/metatemp/overtest/root/"
  shareddir = "/user/metatemp/overtest/root/"
