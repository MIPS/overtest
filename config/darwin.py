"""
Module for basic darwin config
"""
import ConfigFactory

class Config(ConfigFactory.DefaultConfig):
  """
  Basic darwin config
  """
  fqdn = None
  cvs = "/usr/bin/cvs"
  ccs = "/user/rgi_data2/Verify/Darwin/CoreSWTools_1.0.0.0/root/ccs"
  neo = "/user/rgi_data2/Verify/Components/metag/neo/neo"
  python = "/user/rgi_data2/Verify/Darwin/Python_2.7.2/root/bin/python"
  perl = "/usr/bin/perl"
  bitstreams = "/user/rgi_data2/Verify/BitStreams"
  searchPathSep = ':'
