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
  ccs = "/user/rgi_data2/Verify/CentOS-3/CoreSWTools_1.0.0.0/root/ccs"
  neo = "/user/rgi_data2/Verify/Components/metag/neo/neo"
  python = "/user/rgi_data2/Verify/CentOS-3/Python_2.7.2/root/bin/python"
  perl = "/usr/bin/perl"
  bitstreams = "/user/rgi_data2/Verify/BitStreams"
  searchPathSep = ':'
  p4 = '/meta/perforce/bin/p4'
