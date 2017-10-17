"""
Module for a29 config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Class for a29 config
  """
  fqdn = "a29"
  localdir = "/scratch/mpf/overtest/"
  logdir = "/user/leeds.tmp/overtest/root/"
  shareddir = "/scratch/mpf/overtest/"
  python = "/user/rgi_data2/Verify/CentOS-5/Python_2.7.2/root/bin/python"

