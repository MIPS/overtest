import os
from Action import Action
from IMGAction import IMGAction
from Config import CONFIG
import gzip
import yaml
from utils.Utilities import versionCompare

# Run

class A115930(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 115930
    self.name = "Run"

  # Execute the action.
  def run(self):
    da_max_timeout = 0
    metag_inst_root = self.config.getVariable ("METAG_INST_ROOT")
    workdir         = self.config.getVariable ("RA_SOURCE")
    workdir         = os.path.join(workdir, 'metag', 'regressionapps',
                                   'framework', 'performance')
    toolchain       = "gcc"
    target_board    = self.config.getVariable ("Target Board")
    if "FPGA" in target_board:
      implementation = "fpga_tcf"
    elif target_board == "Chorus 2 Metamorph":
      implementation = "silicon_atp120"
    elif target_board == "COMET Metamorph":
      implementation = "silicon_htp221"
    else:
      self.error("Unknown Target Board")
    config          = self.config.getVariable ("RA Config")
    do_apps         = self.config.getVariable ("RA Do Apps")
    run_as          = self.config.getVariable ("RA Run As")
    
    da_max_timeout = self.config.getVariable ("RA Max Timeout")

    env = { 'METAG_INST_ROOT' : metag_inst_root,
            'PATH' : CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo),
                                            CONFIG.getProgramDir(CONFIG.perl),
                                            os.environ['PATH']])
          }

    toolchain_version = self.testrun.getVersion("MetaMtxToolkit")

    if self.testrun.getVersion("MECCToolkit") != None:
      mecc_inst_root = self.config.getVariable ("MECC_INST_ROOT")
      env['MECC_INST_ROOT'] = mecc_inst_root
      env['LM_LICENSE_FILE'] = os.path.join(os.path.expanduser("~"), "licenses", "uncounted.lic")
      toolchain = "mecc"
      toolchain_version = self.testrun.getVersion("MECCToolkit")

    cmd = [CONFIG.perl, "./main.pl"]
    cmd.extend (["--stage=run"])
    cmd.extend (["--compiler=%s" % toolchain])
    cmd.extend (["--compiler-version=%s" % toolchain_version])
    cmd.extend (["--config=%s" % config])
    cmd.extend (["--implementation=%s" % implementation])
    cmd.extend (do_apps.split(','))

    da = self.getResource("Debug Adapter")
    da_name = da.getAttributeValue ("DA Name")
    cmd.extend (["--da=%s" % da_name])
    if run_as != "":
      cmd.extend (["--run-as=%s" % run_as])
    if da_max_timeout > 0:
      cmd.extend (["--da-max-timeout=%s" % da_max_timeout])

    result = self.execute (command=cmd, env=env,
                           workdir=workdir)

    # Exit code 2 says at least one thing worked
    if result != 0 and result != 2:
      self.error ("Failed to run RA")

    cmd[2] = '--stage=analyse'

    result = self.execute (command=cmd, env=env,
                           workdir=workdir)

    # Exit code 2 says at least one thing worked
    if result != 0 and result != 2:
      self.error ("Failed to analyse results")

    cmd = [ 'tar', 'cvfz', 'results.tar.gz', 'results' ]
    result = self.execute (command=cmd, env=env,
                           workdir=workdir)

    if result != 0:
      self.error ("Failed to register log file")

    self.registerLogFile (os.path.join(workdir, "results.tar.gz"))

    yaml_file = os.path.join(workdir, "results", "all.yaml.gz")

    data = yaml.load (gzip.GzipFile (yaml_file, "r"))

    if data == None or not 'tests' in data or data['tests'] == None or len(data['tests']) == 0:
      self.error ("Empty yaml result file")

    for tst_k, tst_v in data['tests'].items():
      result = {}

      if 'run_time' in tst_v:
        result['run_time'] = tst_v['run_time']

      if 'execution_profile' in tst_v:
        if 'issued' in tst_v['execution_profile']:
          result['issued'] = tst_v['execution_profile']['issued']
        if 'idle' in tst_v['execution_profile']:
          result['idle'] = tst_v['execution_profile']['idle']

      if 'binaries' in tst_v:
        for bin_k, bin_v in tst_v['binaries'].items():
          if 'sizes' in bin_v:
            if 'custom' in bin_v['sizes']:
              cst_v = bin_v['sizes']['custom']
              for x in ('app_code', 'app_data', 'lib_code', 'lib_data', 'total_code', 'total_data'):
                if x in cst_v:
                  result[x] = cst_v[x]

      self.testsuiteSubmit (tst_k, tst_v['passed'], extendedresults=result)

    return True
