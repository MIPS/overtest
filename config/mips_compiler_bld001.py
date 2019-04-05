"""
Module for mips-compiler-bld001 config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Class for mips-compiler-bld001 config
  """
  fqdn = "mips-compiler-bld001"
  localdir = "/scratch/overtest/root/"
  logdir = "/scratch/overtest/root/"
  shareddir = "/scratch/overtest/root/"
  python = "/mips/tools/sweng/freeware/python/2.7.13/Linux/bin/python"
  git = "/usr/local/bin/git"
  cores = 48
