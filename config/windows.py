"""
Module for generic windows config
"""
import ConfigFactory

class Config(ConfigFactory.DefaultConfig):
  """
  Class for generic windows config
  """
  fqdn = None
  cvs = "/usr/bin/cvs"
  ccs = "/img/usr/metag/Verify/Windows/CoreSWTools_1.0.0.0/root/ccs"
  neo = "/cygdrive/k/rgi_data2/Verify/Components/metag/neo/neo"
  python = "/img/usr/metag/Verify/Windows/Python_2.7.2/root/bin/python"
  bitstreams = "/cygdrive/k/rgi_data2/Verify/BitStreams"
  searchPathSep = ':'
