"""
Module for cosy02 config
"""
import config.centos45

class Config(config.centos45.Config):
  """
  Class for cosy02 config
  """
  fqdn = "cosy02.kl.imgtec.org"
  localdir = "/home/scratch/overtest/root/"
  logdir = "/home/scratch/overtest/root/"
  shareddir = "/home/scratch/overtest/shared/"
