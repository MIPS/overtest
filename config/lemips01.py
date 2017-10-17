"""
Module for lemips01 config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Class for lemips01 config
  """
  fqdn = "lemips01.le.imgtec.org"
  localdir = "/home/overtest/root/"
  logdir = "/home/overtest/root/"
  shareddir = "/home/overtest/share/"
  git = "/usr/bin/git"
