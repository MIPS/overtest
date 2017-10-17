"""
Module for meta03 config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Class for meta03 config
  """
  fqdn = "meta03.kl.imgtec.org"
  localdir = "/meta/home/overtest/root/"
  logdir = "/meta/home/overtest/root/"
  shareddir = "/user/edatemp/meta/overtest/"
