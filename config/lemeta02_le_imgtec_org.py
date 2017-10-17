"""
Module for lemeta02 config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Class for lemeta02 config
  """
  fqdn = "lemeta02.le.imgtec.org"
  localdir = "/home/ldap/mfortune/overtest/root/"
  logdir = "/home/ldap/mfortune/overtest/root/"
  shareddir = "/share/meta/shared/overtest/"
