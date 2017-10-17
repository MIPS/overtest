import os

from Action import Action
from Config import CONFIG

# FetchMECCScripts

class A114691(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 114691
    self.name = "FetchMECCScripts"

  # Execute the action.
  def run(self):
    host = self.getResource('Execution Host')
    p4port = str(host.getAttributeValue('P4PORT'))

    COBIT_INST_ROOT = self.config.getVariable("COBIT_INST_ROOT")

    root = self.getWorkPath()

    env = { 'PATH' : CONFIG.makeSearchPath([os.path.join(COBIT_INST_ROOT, 'bin'),
                                            os.environ['PATH']]),
            'P4PORT' : p4port,
            'P4USER' : 'xbuild.meta',
          }

    command = ['p4_cmp', 'fetch', 'MECCToolkit', '--partial=mecc/release/...']
    if self.version == 'CHANGELIST':
        changelist = self.config.getVariable('MECCSCRIPTS_FETCH_CHANGELIST')
        command.append('--changeset=%s' % changelist)
        location = self.config.getVariable('MECCSCRIPTS_FETCH_LOCATION')
        command.append('--location=%s' % location)
    else:
        command[-1] = command[-1] + ':%s' % self.version
    command.append(root)

    if self.execute(env=env, command=command):
      self.error("Failed to fetch source")

    self.config.setVariable("MECC_RELEASE_ROOT", root)

    return self.success()
