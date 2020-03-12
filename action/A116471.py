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
import os
from Action import Action
import yaml
import sets

# Results

class A116471(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116471
    self.name = "Results"

  # Execute the action.
  def run(self):
    dir_cadese = os.path.join ('/user', 'local_cosy')

    workdir = os.path.join (self.config.getVariable ("ST_SOURCE_ROOT"), "supertest")
    spoofStdin = [[],
                  [ "cd", "results/log" ],
                  [ "for f in *; do if [ -d \"$f\" ]; then ../../bin/log-report -tables $f | ../../do-tests/overtest_results_parser.pl > $f.2.yaml; fi; done" ],
                  [ "rm results.2.yaml" ],
                  [ "cat *.2.yaml >results.2.yaml" ],
                  [ "exit" ]
                 ]
    spoofStdin = [ ' '.join(x) for x in spoofStdin ]
    cmd = [ "product", "enter" ]
    env = { 'PATH': '%s/product/bin:%s/cadese/bin:%s/sccs/bin:%s' % (dir_cadese, dir_cadese, dir_cadese, os.getenv ('PATH') ),
          }
    result = self.execute(env=env, command=cmd, workdir=workdir, spoofStdin='\n'.join(spoofStdin))

    if not result == 0:
      self.error ("Failed to run command")

    yaml_file = os.path.join(workdir, "build", "results", "log", "results.2.yaml")

    self.registerLogFile (yaml_file)

    data = yaml.load (open (yaml_file, "r"))

    unexpected_fail = 0
    grand_total = {}
    for cfgnam, cfgdat in data.items():
      total = cfgdat['t'].copy()
      for tmp in ['unexpected_failed', 'expected_failed', 'unexpected_check', 'expected_check']:
        total[tmp] = len(cfgdat[tmp]) if tmp in cfgdat else 0
      del total['fail']
      del total['check']

      testgrps  = sets.Set(cfgdat['c'].keys())
      testgrps |= sets.Set(cfgdat['r'].keys())
      for tstnam in testgrps:
        extended_results = {}
        extended_fail = 0
        for prefix, subset in [("compile", 'c'), ("run", 'r')]:
          if subset not in cfgdat:
            return self.error ("Invalid subset key '%s' when working on %s %s %s" % (subset, cfgnam, tstnam, subset))
          elif tstnam not in cfgdat[subset]:
            cfgdat[subset][tstnam] = { 'pass' : 0, 'fail' : 0, 'check' : 0 }
          extended_results.update(dict([("%s_%s"%(prefix,x),y) for x, y in cfgdat[subset][tstnam].items()]))
          extended_fail += extended_results['%s_fail'%prefix] if '%s_fail'%prefix in extended_results else 0
        self.testsuiteSubmit ("%s %s"%(tstnam,cfgnam), extended_fail == 0, extendedresults=extended_results)

      for tmpkey, tmpval in total.items():
        grand_total[tmpkey] = grand_total[tmpkey] + tmpval if tmpkey in grand_total else tmpval
      unexpected_fail += len(cfgdat['unexpected_failed']) if 'unexpected_failed' in cfgdat else 0

    if unexpected_fail == 0:
      return self.success(extendedresults=grand_total)
    else:
      return self.failure(extendedresults=grand_total)
