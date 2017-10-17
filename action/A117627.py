import os
from Action import Action
from IMGAction import IMGAction

# MeOS

class A117627(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117627
    self.name = "MeOS"

  # Execute the action.
  def run(self):
    workdir = self.getWorkPath()

    host = self.getResource ("Execution Host")
    da = self.getResource ("Debug Adapter")

    cvsroot = host.getAttributeValue ("LEEDS CVSROOT")

    METAG_INST_ROOT = self.config.getVariable ("METAG_INST_ROOT")

    version = self.version.split('.')
    meos_version = version[0:-1]
    meos_board   = version[-1]

    if not self.cvsCheckout(module="codescape/meos",
                            cvsroot=cvsroot,
                            tag="MEOS_%s_TAG" % '_'.join(meos_version)):
      atp120dp_ocm
      self.error("Failed to check out meos source")

    cmd = [ 'make',
            'BOARD=%s' % meos_board,
            'DA=%s' % da.getAttributeValue("DA Name"),
          ]

    env = {}
    env['METAG_INST_ROOT'] = METAG_INST_ROOT

    if self.execute(workdir=os.path.join(workdir, 'codescape', 'meos'),
                    command=cmd,
                    env=env) != 0:
      self.error("MeOS Tests failed")

    return self.success()
