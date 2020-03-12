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
import OvtDB
import sets

try:
  import yaml
except ImportError:
  supports_yaml = False
else:
  supports_yaml = True

class TestrunIdExporter:
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
    print "-c <category> --category=<category> An action category to search by"
    print "-a <action>   --action=<action>     An action in a category to search by"
    print "-v <version>  --version=<version>   A specific version of an action"
    print "              --and                 Join multiple search terms with logical and"
    print "              --or                  Join multiple search terms with logical or"
    print "              --sortby=<action>     Sort results by a given action"
    print "-f <file>     --file=<file>         Output results to a file"
    print "-h            --help                This help"
    print ""
    print "All search terms are either joined by 'and' or 'or'. No combinations are"
    print "supported"
    sys.exit (exitcode)

  def exportData(self, args):
    try:
      opts, args = getopt.getopt (args, "c:a:v:f:h", ["help", "file=", "category=", "action=", "version=", "sortby=", "and", "or"])
    except getopt.GetoptError, e:
      self.usage (2, str(e))

    if not supports_yaml:
      self.error ("This requires YAML support but this was not available")
      sys.exit (4)

    match_specs = []
    mode = '='
    category_name = None
    action_name = None
    version_name = None
    sortby = None
    yaml_file = sys.stdout

    for (o, a) in opts:
      if o in ("-c","--category"):
        category_name = a
        action_name = None
      elif o in ("-a","--action"):
        action_name = a
        if category_name == None:
          self.error("A category is required before action arguments")
          sys.exit(2)
      elif o in ("-v","--version"):
        if mode == None:
          self.error("Multiple actions/versions must be joined with --and/--or")
          sys.exit(2)
        version_name = a
        match_specs.append ((mode, category_name, action_name, version_name))
        mode = None
      elif o in ("-h","--help"):
        self.usage(1)
      elif o in ("-f","--file"):
        try:
          yaml_file = open(a, "w")
        except IOError:
          self.error("Unable to open %s for writing" % a)
          sys.exit(1)
      elif o == '--and':
        if len(match_specs) == 0:
          self.error("At least one version must be present before joining")
          sys.exit(2)
        mode = '&'
      elif o == '--or':
        if len(match_specs) == 0:
          self.error("At least one version must be present before joining")
          sys.exit(2)
        mode = '|'
      elif o == "--sortby":
        sortby = a
      else:
        self.usage(1)

    if len(match_specs) == 0:
      self.error("Please specify at least one search term")
      sys.exit(2)

    results = {}
    for mode, category_name, action_name, version_name in match_specs:
      subresults = {}
      catactvers = OvtDB.OvtDBActionCategory_Action_VersionedAction.find(self.ovtDB,
                                                                         category_name=OvtDB.LikeCondition(None, category_name),
                                                                         action_name=OvtDB.LikeCondition(None, action_name),
                                                                         version_name=OvtDB.LikeCondition(None, version_name))
      for catactver in catactvers:
        actioncategory, action, version = catactver.split()
        for testrun_action_testrun in version.testrun_actions_testrun(self.ovtDB) or []:
          testrun_action, testrun = testrun_action_testrun.split ()
          subresults[testrun.id] = testrun

      if mode == '=':
        results = subresults
      elif mode == '|':
        for k,v in subresults.items():
          if k not in results:
            results[k] = v
      elif mode == '&':
        for k,v in results.items():
          if k not in subresults:
            del results[k]
      else:
        assert False

    if sortby != None:
      tmp = OvtDB.OvtDBTestrunAction_VersionedAction_Action.find (self.ovtDB, testrun_action_testrunid=tuple(results.keys()))
      results = dict([(k, v) for k, v in results.items()])
      # import pprint
      # pp = pprint.PrettyPrinter()
      # pp.pprint(results)
      for testrun_action2 in tmp:
        testrun_action, version, action = testrun_action2.split()
        id = testrun_action.testrunid
        if action.name == sortby:
          results[id] = (version, results[id])
      # pp.pprint(results)
      results = [ (key and key.name, testrun.id) for key, testrun in sorted(results.values(), key=lambda x: OvtDB.OvtDBVersionedAction.sortkey(x[0])) ]
      yaml_out = [ testrun for key, testrun in results ]
    else:
      yaml_out = [ testrun for testrun in results ]

    yaml.dump (yaml_out, sys.stdout, default_flow_style = False, explicit_start = True)

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

