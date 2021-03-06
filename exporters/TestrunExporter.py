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
import sys
import os
import getopt
from Config import CONFIG
import ConfigFactory
from OvertestExceptions import *
try:
  import yaml
except ImportError:
  supports_yaml = False
else:
  supports_yaml = True

class TestrunExporter:
  ovtDB = None

  def __init__(self, _ovtDB):
    self.ovtDB = _ovtDB
    self.debug_enabled = False

  def usage(self, exitcode, error = None):
    """
    Display the usage
    """
    if error != None:
      self.error(error)
      print ""
    print "Usage:"
    print "  -i <id>   --testrunid=<id> Specify the testrun"
    print "            --help-sample    Emit a sample file explaining the format"
    print "            --automatic      Show automatic configuration as well"
    print "  -f <file> --file=<file>    Specify file to write output to"
    sys.exit (exitcode)

  def help_sample(self):
    print "# Important Information"
    print "# 1) mapping collections are unordered and will not appear in this"
    print "#    order"
    print "# 2) Unicode strings are not supported"

    print "---"
    print "testrunid: <decimal-number>   # The testrun id specified by --testrunid=<id>"
    print "description: <string>         # Description of the testrun"
    print "groupname: <string>           # Name of the testrun group"
    print "user: <string>                # User who ran the test"
    print "priority: <decimal-number>    # The priority to run the test as"
    print "concurrency: <decimal-number> # The number of jobs to run in parallel"
    print "deptestrunid: <decimal-number># The testrun that must complete before this one"
    print "autoarchive: <boolean>        # Whether to archive on success"
    print "usegridengine: <boolean>      # Whether to run on a grid engine"
    print "definition:"
    print "  # This collection maps action categories to versions of actions that were used"
    print "  Linux:"
    print "    # This collection maps an action to the version used"
    print "    META Linux Bootloader: Latest"
    print "configuration:"
    print "  # This collection maps configuration groups to settings"
    print "  Linux Kernel:"
    print "    # This collection maps a configuration option to a setting"
    print "    Bootloader Board: ''"
    print "resources:"
    print "  # This collection maps resource types to resource requirements"
    print "  Execution Host:"
    print "    require:"
    print "      # This collection maps attributes to the chosen values"
    print "      Specific Host: Leeds Meta 01"

  def exportData(self, args):
    try:
      opts, args = getopt.getopt (args, "i:f:h", ["testrunid=", "file=", "automatic", "help", "help-sample"])
    except getopt.GetoptError, e:
      self.usage (2, str(e))

    if not supports_yaml:
      self.error ("This requires YAML support but this was not available")
      sys.exit (4)

    testrunid = None
    automatic_config = False
    yaml_file = sys.stdout

    for (o, a) in opts:
      if o in ("-i", "--testrunid"):
        try:
          testrunid = int(a)
        except ValueError:
          self.error("Testrun id specified is not numeric: %s" % a)
          sys.exit(1)
      elif o == "--automatic":
	automatic_config = True
      elif o in ("-f", "--file"):
        try:
          yaml_file = open(a, "w")
        except IOError:
          self.error("Unable to open %s for writing" % a)
          sys.exit(1)
      elif o in ("-h","--help"):
        self.usage(1)
      elif o == "--help-sample":
        return self.help_sample ()

    if testrunid == None:
      self.error("Please specify a testrunid")
      sys.exit(1)

    yaml_out = {}

    testrun_detail = self.ovtDB.simple.getTestrunById(testrunid)
    if testrun_detail == None:
      self.error("Unable to find testrun with id: %s" % testrunid)
      sys.exit(1)
    
    yaml_out['testrunid'] = int(testrunid)
    yaml_out['description'] = str(testrun_detail['description'])
    yaml_out['concurrency'] = int(testrun_detail['concurrency'])
    yaml_out['priority'] = int(testrun_detail['priority'])
    yaml_out['deptestrunid'] = testrun_detail['deptestrunid']
    yaml_out['autoarchive'] = bool(testrun_detail['autoarchive'])
    yaml_out['usegridengine'] = bool(testrun_detail['usegridengine'])
    yaml_out['user'] = str(self.ovtDB.simple.getUserById(testrun_detail['userid'])['username'])
    yaml_out['group'] = str(self.ovtDB.simple.getTestrunGroupById(testrun_detail['testrungroupid']))
    definition = self.ovtDB.getTestrunDefinition(testrunid)
    yaml_out['definition'] = []
    for id in definition[1]:
      def2 = {}
      yaml_out['definition'].append({str(definition[0][id]["data"]): def2})
      for id2 in definition[0][id]['related'][1]:
        id3 = definition[0][id]['related'][0][id2]['related'][1][0]
        def2[str(definition[0][id]['related'][0][id2]["data"])] = \
          str(definition[0][id]['related'][0][id2]['related'][0][id3]['data'])

    configuration = self.ovtDB.getTestrunConfiguration(testrunid, automatic=automatic_config)
    yaml_out['configuration'] = []
    for id in configuration[1]:
      def2 = {}
      yaml_out['configuration'].append({str(configuration[0][id]["data"]): def2})
      for id2 in configuration[0][id]['related'][1]:
        id3 = configuration[0][id]['related'][0][id2]['related'][1][0]
        def2[str(configuration[0][id]['related'][0][id2]["data"])] = \
          str(configuration[0][id]['related'][0][id2]['related'][0][id3]['data'])

    resources = self.ovtDB.getTestrunRequirements(testrunid)
    yaml_out['resources'] = []
    for id in resources[1]:
      def2 = {'require': {}}
      yaml_out['resources'].append({str(resources[0][id]["data"]): def2})
      def2 = def2['require']
      for id2 in resources[0][id]['related'][1]:
        id3 = resources[0][id]['related'][0][id2]['related'][1][0]
        def2[str(resources[0][id]['related'][0][id2]["data"])] = \
          str(resources[0][id]['related'][0][id2]['related'][0][id3]['data'])

    yaml.dump (yaml_out, yaml_file, default_flow_style = False, explicit_start = True)

  def debug(self, debug):
    """
    Print an debug message
    """
    if self.debug_enabled:
      print "DEBUG: %s"%debug

  def error(self, error):
    """
    Print an error message
    """
    print "ERROR: %s"%error

