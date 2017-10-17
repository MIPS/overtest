"""
Module for klmeta05 config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Class for klmeta05 config
  """
  fqdn = "klmeta05.kl.imgtec.org"
  localdir = "/meta/home/overtest/root/"
  logdir = "/user/metatemp/overtest/root/"
  shareddir = "/user/metatemp/overtest/root/"
