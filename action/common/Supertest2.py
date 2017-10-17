import os
from action.Action import Action
from Config import CONFIG

class SuperTestAction(Action):
  def __init__(self, data):
    Action.__init__(self, data)

  def get_mode(self):
    assert False

  def get_testgroups(self):
    return []

  def get_testgroupopts(self):
    return [ "--testgrp=%s" % x for x in self.get_testgroups() ]

  # Execute the action.
  def run(self):
    dir_cadese = os.path.join ('/user', 'local_cosy')
    serverhost = self.getResource("Execution Host").getHostName()

    workdir = os.path.join (self.config.getVariable ("ST_SOURCE_ROOT"), "supertest")
    spoofStdin = [[],
                  [ "export", "MECC_INST_ROOT='%s'" % self.config.getVariable("MECC_INST_ROOT") ],
                  [ "export", "LM_LICENSE_FILE='%s'" % os.path.join(os.path.expanduser("~"), "licenses", "uncounted.lic")],
                  [ "export", "METAG_INST_ROOT='%s'" % self.config.getVariable("METAG_INST_ROOT") ],
                  [ "export", "METAG_FSIM_ROOT='%s'" % self.config.getVariable("METAG_FSIM_ROOT") ],
                  [ "export", "PATH=%s" % CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo),
                                                                 "$PATH"])],
                  [ "export", "ALLOW_REMOTE_HASP=1" ],
                  [ "./do-tests/%s-all.pl" % self.get_mode(),
                    "--results=$PWD/results",
                    "--serverhost=%s" % serverhost,
                  ] + self.get_testgroupopts(),
                  [ "exit" ]
                 ]
    spoofStdin = [ ' '.join(x) for x in spoofStdin ]
    spoofStdin = '\n'.join(spoofStdin)

    print "BEGIN STDIN"
    print spoofStdin
    print "END STDIN"

    cmd = [ "product", "enter" ]

    env = { 'PATH': CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo),
                                           '%s/product/bin:%s/cadese/bin:%s/sccs/bin' % (dir_cadese,
                                                                                         dir_cadese,
                                                                                         dir_cadese),
                                           os.environ['PATH']])
          }
    result = self.execute(env=env, command=cmd, workdir=workdir, spoofStdin=spoofStdin)

    if not result == 0:
      self.error ("Failed to run command")

    return self.success ()
