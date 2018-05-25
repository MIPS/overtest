"""
Module for CentOS 4.5 config
"""
import config.linux

class Config(config.linux.Config):
  """
  CentOS 4.5 default config
  """
  python = "/mips/tools/sweng/freeware/python/2.7.13/Linux/bin/python"
  git = "/usr/bin/git"
  perl = "/usr/bin/perl"
  cmake = "/mips/tools/sweng/freeware/cmake/2.8.12.2/bin/cmake"
