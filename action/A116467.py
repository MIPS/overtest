import os
from Action import Action
from Config import CONFIG
import yaml

# CheckInitial

class A116467(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116467
    self.name = "CheckInitial"

  # Execute the action.
  def run(self):
    dir_cadese = os.path.join ('/user', 'local_cosy')

    workdir = os.path.join (self.config.getVariable ("ST_SOURCE_ROOT"), "supertest")
    spoofStdin = [[],
                  [ "cd", "results/log" ],
                  [ "for f in *; do ../../bin/log-report -tables $f | ../../do-tests/overtest_results_parser.pl > $f.yaml; done" ],
                  [ "cat *.yaml >results.yaml" ],
                  [ "exit" ]
                 ]
    spoofStdin = [ ' '.join(x) for x in spoofStdin ]
    cmd = [ "product", "enter" ]
    env = { 'PATH': CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo),
                                           '%s/product/bin:%s/cadese/bin:%s/sccs/bin' % (dir_cadese, 
                                                                                         dir_cadese, 
                                                                                         dir_cadese),
                                           os.environ['PATH']])
          }
    result = self.execute(env=env, command=cmd, workdir=workdir, spoofStdin='\n'.join(spoofStdin))

    if not result == 0:
      self.error ("Failed to run command")

    yaml_file = os.path.join(workdir, "build", "results", "log", "results.yaml")

    self.registerLogFile (yaml_file)

    data = yaml.load (open (yaml_file, "r"))

    failed = [cfgdat for cfgnam, cfgdat in data.items()]
    failed = [cfgdat['unexpected_failed'] if 'unexpected_failed' in cfgdat else [] for cfgdat in failed]
    failed = [x for y in failed for x in y ]

    if len(failed) == 0:
      return self.success()
    else:
      self.error("Sanity check failed")
