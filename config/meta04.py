"""
Module for meta04 config
"""
import config.centos45

class Config(config.centos45.Config):
  """
  Class for meta04 config
  """
  fqdn = "meta04.kl.imgtec.org"
  localdir = "/meta/home/overtest/root/"
  logdir = "/meta/home/overtest/root/"
  shareddir = "/user/edatemp/meta/overtest/"
