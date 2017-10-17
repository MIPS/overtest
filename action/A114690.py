import os
import glob
from utils.Utilities import versionCompare
from Action import Action
from IMGAction import IMGAction
from Config import CONFIG

# BuildMECCToolkit

class A114690(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 114690
    self.name = "BuildMECCToolkit"

  # Execute the action.
  def run(self):
    host = self.getResource('Execution Host')
    p4port = str(host.getAttributeValue('P4PORT'))

    workdir = self.config.getVariable ("MECC_RELEASE_ROOT")
    metag_inst_root = self.config.getVariable ("METAG_INST_ROOT")

    COBIT_INST_ROOT = self.config.getVariable("COBIT_INST_ROOT")

    cmp_ver = self.testrun.getVersion ("BuildMECCToolkit")

    license_file = os.path.join(os.path.expanduser("~"), "licenses")

    env = {'P4PORT' : p4port,
           'P4USER' : 'xbuild.meta',
          }
    env['PATH'] = CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo),
                                         os.path.join(COBIT_INST_ROOT, 'bin'),
                                         os.environ['PATH']])
    cmd = [ './scripts/all.sh', '--TOOLKIT_VERSION', cmp_ver, 
                                '--METAG_INST_ROOT', metag_inst_root, 
                                '--LICENSE_FILE', license_file]
    
    if bool(self.config.getVariable("MECC_BOOTSTRAP")):
      cmd.append('--BOOTSTRAP')

    if not self.config.getVariable ("MECC_DO_WINDOWS"):
      cmd.extend (["--SKIP_WINDOWS"])

    mingw_root = self.config.getVariable ("GCCMINGW_ROOT")
    cmd.extend(['--MINGW', mingw_root])

    env['EXTRA_PATH'] = CONFIG.makeSearchPath([])

    result = self.execute(env=env, command=cmd, workdir="%s/mecc/release"%workdir)
    if result != 0:
      self.error ("Could not build MECC")

    return self.success ()
