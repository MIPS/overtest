import os

from Action import Action
from Config import CONFIG

# Fetch

class A116456(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116456
    self.name = "Fetch"

  # Execute the action.
  def run(self):
    host = self.getResource('Execution Host')
    p4port = str(host.getAttributeValue('P4PORT'))

    COBIT_INST_ROOT = self.config.getVariable("COBIT_INST_ROOT")

    root = self.getWorkPath()

    env = { 'PATH' : CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo),
                                            os.path.join(COBIT_INST_ROOT, 'bin'),
                                            os.environ['PATH']]),
            'P4PORT' : p4port,
            'P4USER' : 'xbuild.meta',
          }

    command = ['p4_cmp', 'fetch', 'SuperTest']
    if self.version == 'CHANGELIST':
        changelist = self.config.getVariable('ST_FETCH_CHANGELIST')
        command.append('--changeset=%s' % changelist)
        command.append('--location=//meta/swcore/cosy/code/supertest/MAIN/supertest/build/xySuperTest.xyf')
    else:
        command[-1] = command[-1] + ':%s' % self.version
    command.append(root)

    if self.execute(env=env, command=command):
      self.error("Failed to fetch source")

    self.config.setVariable("ST_SOURCE_ROOT", root)

    return self.success()
