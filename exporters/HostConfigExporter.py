#  Copyright (C) 2012-2020 MIPS Tech LLC
#  Written by Matthew Fortune <matthew.fortune@imgtec.com> and
#  Daniel Sanders <daniel.sanders@imgtec.com>
#  This file is part of Overtest.
#
#  Overtest is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3, or (at your option)
#  any later version.
#
#  Overtest is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with overtest; see the file COPYING.  If not, write to the Free
#  Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
#  02110-1301, USA.
"""
Module to export host configuration
"""
import sys
import getopt
from Config import CONFIG
import ConfigFactory

try:
  import yaml
except ImportError:
  SUPPORTSYAML = False
else:
  SUPPORTSYAML = True

class HostConfigExporter:
  """
  Class to manage exporting host configuration
  """

  def __init__(self, ovtdb):
    """
    Basic constructor
    """
    self.ovtDB = ovtdb
    self.debugEnabled = False

  def usage(self, exitcode, error = None):
    """
    Display the usage
    """

    if error != None:
      self.error(error)
      print ""
    print "Usage:"
    print "            --host=<name> Specify the host"
    print "  -f <file> --file=<file> Write output to a file"
    print "  -h        --help        This help"
    sys.exit (exitcode)

  def exportData(self, args):
    """
    Performs the export of host configuration to yaml
    """

    try:
      opts, args = getopt.getopt (args, "f:h", ["file=","help","host="])
    except getopt.GetoptError, ex:
      self.usage (2, str(ex))

    if not SUPPORTSYAML:
      self.error ("This requires YAML support but this was not available")
      sys.exit (4)

    host = None

    yaml_file = sys.stdout

    for (o, a) in opts:
      if o == "--host":
        host = a
      elif o in ("-h","--help"):
        self.usage(1)
      elif o in ("-f","--file"):
        try:
          yaml_file = open(a, "w")
        except IOError:
          self.error("Unable to open %s for writing" % a)
          sys.exit(1)

    yamlOut = {}

    if host == None:
      hostConfig = CONFIG
    else:
      hostConfig = ConfigFactory.configFactory(host)

    yamlOut['fqdn']            = hostConfig.host or host
    yamlOut['localdir']        = hostConfig.localdir
    yamlOut['shareddir']       = hostConfig.shareddir
    yamlOut['logdir']          = hostConfig.logdir
    yamlOut['cvs']             = hostConfig.cvs
    yamlOut['ccs']             = hostConfig.ccs
    yamlOut['neo']             = hostConfig.neo
    yamlOut['git']             = hostConfig.git
    yamlOut['python']          = hostConfig.python
    yamlOut['perl']            = hostConfig.perl
    yamlOut['p4']              = hostConfig.p4
    yamlOut['bitstreams']      = hostConfig.bitstreams
    yamlOut['search_path_sep'] = hostConfig.searchPathSep

    yaml.dump (yamlOut, yaml_file, default_flow_style = False, explicit_start = True)

  def debug(self, debug):
    """
    Print an debug message
    """
    if self.debugEnabled:
      print "DEBUG: %s" % debug

  def error(self, error):
    """
    Print an error message
    """
    print "ERROR: %s" % error

