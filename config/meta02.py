"""
Module for meta02 Config
"""
import config.linux

class Config(config.linux.Config):
  """
  Class for meta02 config
  """
  fqdn = "meta02.kl.imgtec.org"
  localdir = "/meta/home/overtest/root/"
  logdir = "/meta/home/overtest/root/"
  shareddir = "/user/edatemp/meta/overtest/"
