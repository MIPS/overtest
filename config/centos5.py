"""
Module for CentOS 5 config
"""
import config.centos45

class Config(config.centos45.Config):
  """
  CentOS 5 default config
  """
  python = "/mips/tools/sweng/freeware/python/2.7.13/Linux/bin/python"
  cmake = "/mips/tools/sweng/freeware/cmake/2.8.12.2/bin/cmake"
  git = "/usr/bin/git"
