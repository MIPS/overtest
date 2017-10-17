import os
from Action import Action
from IMGAction import IMGAction
from Config import CONFIG

# EEMBC

class A113829(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 113829
    self.name = "EEMBC"

  # Execute the action.
  def run(self):
    host = self.getResource('Execution Host')
    p4port = str(host.getAttributeValue('P4PORT'))
    COBIT_INST_ROOT = self.config.getVariable("COBIT_INST_ROOT")

    env = { 'PATH' : CONFIG.makeSearchPath([os.path.join(COBIT_INST_ROOT, 'bin'),
                                            os.environ['PATH']]),
            'P4PORT' : p4port,
            'P4USER' : 'xbuild.meta',
          }

    if self.version == 'CHANGELIST':
      root = self.getWorkPath()

      command = ['p4_cmp', 'fetch', '--writable', 'EEMBC']
      if self.version == 'CHANGELIST':
          changelist = self.config.getVariable('EEMBC_FETCH_CHANGELIST')
          command.append('--changeset=%s' % changelist)
          command.append('--location=//meta/swcore/code/restricted/eembc/MAIN/eembc/xyEEMBC.xyf')
      else:
          command[-1] = command[-1] + ':%s' % self.version
      command.append(root)

      if self.execute(env=env, command=command):
        self.error("Failed to fetch source")

      self.config.setVariable ("EEMBC Source", root)

      result = self.execute (command=["scripts/initialise.sh"],
                             workdir="%s/eembc"%root)

      if result != 0:
        self.error ("Failed to initialise EEMBC")

      return True
    else:
      workdir = self.getWorkPath()
      # The version to fetch is anything up to the first space, anything
      # following the space is a comment does not affect the get_source
      # command
      neo_cmp_ver = self.version.split(" ")[0]

      # The environment is set at this point
      # P4PORT and P4USER are required
      if not self.neoGetSource (workdir, "EEMBC", neo_cmp_ver, env):
        self.error ("Failed to get source")
      self.config.setVariable ("EEMBC Source", workdir)

      result = self.execute (command=["scripts/initialise.sh"],
                             workdir="%s/eembc"%workdir)

      if result != 0:
        self.error ("Failed to initialise EEMBC")

      return True
