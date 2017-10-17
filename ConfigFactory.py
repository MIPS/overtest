"""
A factory for creating Config objects based on a hostname
"""
import os
import sys

def getClass( kls ):
  """
  Obtain the Config class from the appropriate module
  """
  parts = kls.split('.')
  mod = __import__( kls )
  for comp in parts[1:]:
    mod = getattr(mod, comp)
  mod = mod.Config
  return mod

def configFactory(hostname):
  """
  Create a class to represent the current host's config
  """
  hostname = hostname.replace(".", "_").replace("-", "_")
  try:
    if 'JOB_ID' in os.environ:
      classObj = getClass ("config.uge")
    else:
      classObj = getClass ("config.%s"%hostname)
  except ImportError:
    # Fall back to default config
    if sys.platform == "darwin":
      classObj = getClass ("config.darwin")
    elif 'WINDIR' in os.environ:
      classObj = getClass ("config.windows")
    else:
      classObj = getClass ("config.centos5")

  obj = classObj ()

  obj.hostname = hostname

  return obj

class DefaultConfig:
  """
  Basic config for hosts to inherit
  """
  host          = None
  localdir      = ""
  logdir        = ""
  shareddir     = ""
  cvs           = ""
  ccs           = ""
  neo           = ""
  perl          = ""
  python        = ""
  python_exe    = ""
  bitstreams    = ""
  git           = ""
  searchPathSep = None
  p4            = ""

  def __init__(self):
    """
    Null constructor
    """
    pass

  def getProgramDir(self, prog):
    """
    Get the dirname of the specified program
    """
    return os.path.split(prog)[0]
  
  def makeSearchPath(self, lst):
    """
    Construct a new PATH variable suitable for the host OS
    """
    return self.searchPathSep.join(lst)
