"""
Module for basic linux config
"""
import ConfigFactory

class Config(ConfigFactory.DefaultConfig):
  """
  Basic linux config (minimum version supported CentOS 3.8)
  """
  fqdn = None
  cvs = "/usr/bin/cvs"
  python = "/mips/tools/sweng/freeware/python/2.7.13/Linux/bin/python"
  perl = "/usr/bin/perl"
  bitstreams = "/user/rgi_data2/Verify/BitStreams"
  searchPathSep = ':'
  p4 = '/meta/perforce/bin/p4'
  gitref = "/projects/mipssw/git"
