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

class ResultsExporter:
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
    print "  -f <file> --file=<file>    Write output to a file"
    print "  -h        -help            This help"
    sys.exit (exitcode)

  def help_sample(self):
    print "# Important Information"
    print "# 1) mapping collections are unordered and will not appear in this"
    print "#    order"
    print "# 2) Unicode strings are not supported"
    print "---"
    print "testrunid: <decimal-number> # The testrun id specified by --testrun=<id>"
    print "status:  <string>         # The status of the testrun. Most commonly 'COMPLETED'"
    print "                          # or 'ABORTED'"
    print "results:"
    print "  # This collection maps each testsuite to its tests"
    print "  <string>: # The test suite name"
    print "    # This collection maps each test to its results"
    print "    <string>: # The test name"
    print "      # This collection contains the results common to"
    print "      # all testsuites"
    print "      passed:  <boolean> # True/False depending on whether the test passed or"
    print "                         # failed"
    #print "      testrunactionid: <decimal-number> # The id of the test. "
    print "      version: <string>  # The version of the results. Some testsuites version"
    print "                         # their results to avoid rerunning identical tests"
    print "      extended:"
    print "        # This collection contains the results specific to this testsuite"
    print "        # (e.g. time/size/md5sum)"
    print "        <string>: <any-type> # Maps a value to a field, the type is defined"
    print "                             # by the testsuite"
    print "debug: <undefined> # Reserved for debugging information for developing this"
    print "                   # exporter"

  def exportData(self, args):
    try:
      opts, args = getopt.getopt (args, "f:hi:", ["testrun=","testrunid=","file=","help","help-sample"])
    except getopt.GetoptError, e:
      self.usage (2, str(e))

    if not supports_yaml:
      self.error ("This requires YAML support but this was not available")
      sys.exit (4)

    testrun_id = None
    yaml_file = sys.stdout

    for (o, a) in opts:
      if o in ("--testrun","--testrunid",'-i'):
        testrun_id = a
      elif o in ("-f","--file"):
        try:
          yaml_file = open(a, "w")
        except IOError:
          self.error("Unable to open %s for writing" % a)
          sys.exit(1)
      elif o in ("-h","--help"):
        self.usage(1)
      elif o == "--help-sample":
        return self.help_sample ()

    yaml_out = {}

    yaml_out['testrunid'] = testrun_id

    suite_ids = self.ovtDB.getTestsuitesInTestrun (testrun_id).keys()

    yaml_out['results'] = {}
    for suite_id in suite_ids:
      suite_nam = str(self.ovtDB.simple.getTestsuiteById(suite_id))
      suite_out = {}

      for tst_k, tst_v in self.ovtDB.getTestResult (testrun_id, [], suite_id).items():
        res_out = {}
        res_out['passed']          = tst_v['pass']
        res_out['version']         = str(tst_v['version'])

        ext_out = {}
        for ext_k, ext_v in tst_v['extended'].items():
          ext_out[str(ext_k)] = ext_v if not isinstance(ext_v, unicode) else str (ext_v)
        res_out['extended'] = ext_out
        suite_out[str(tst_k)] = res_out

      yaml_out['results'][suite_nam] = suite_out
    yaml_out['status'] = str(self.ovtDB.getTestrunRunstatus (testrun_id))

#    yaml_out['debug'] = {}
#    yaml_out['debug']['suites'] = suite_ids
#    yaml_out['debug']['res'] = []
#    for k in suite_ids:
#      yaml_out['debug']['res'].append(self.ovtDB.getTestResult (testrun_id, [], k))

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

