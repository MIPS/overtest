"""
Module for meta05 config
"""
import config.centos45

class Config(config.centos45.Config):
  """
  Class for meta05 config
  """
  fqdn = "meta05.kl.imgtec.org"
  localdir = "/meta/home/overtest/root/"
  logdir = "/meta/home/overtest/root/"
  shareddir = "/user/edatemp/meta/overtest/"
