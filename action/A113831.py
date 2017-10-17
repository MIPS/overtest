import os
import shlex
from utils.Utilities import versionCompare
from Action import Action
from common.EEMBC import EEMBCAction
from Config import CONFIG
import glob
import tarfile
import csv
import sets

# RunEEMBC

class A113831(Action, EEMBCAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 113831
    self.name = "RunEEMBC"

  # Execute the action.
  def run(self):
    metag_inst_root = self.config.getVariable ("METAG_INST_ROOT")
    workdir         = self.config.getVariable ("EEMBC Source")
    toolchain       = "metagcc"
    platform        = self.config.getVariable ("EEMBC Platform")
    cq_stat         = self.config.getVariable ("EEMBC CQStat")
    benchmark       = self.config.getVariable ("EEMBC Benchmarks")
    uuencode        = self.config.getVariable ("EEMBC UUENCODE")
    extra           = shlex.split (self.config.getVariable ("EEMBC Arbitrary"))
    run_as          = self.config.getVariable ("EEMBC Run As")
    cqstat_out      = self.config.getVariable ("EEMBC CQStat Output")
    exec_method     = self.version.split('.')[-1]

    env = { 'METAG_INST_ROOT' : metag_inst_root,
            'PATH' : CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo), os.environ['PATH']])
          }

    if self.testrun.getVersion("MECCToolkit") != None:
      mecc_inst_root = self.config.getVariable ("MECC_INST_ROOT")
      env['MECC_INST_ROOT'] = mecc_inst_root
      env['LM_LICENSE_FILE'] = os.path.join(os.path.expanduser("~"), "licenses", "uncounted.lic")
      toolchain = "metamecc"

    cmd = ["scripts/build.sh"]
    # cmdoptions are options suitable for both building and analysing results
    cmdoptions = ["--toolchains", toolchain]
    cmdoptions.extend (["--platforms",  platform])
    if cq_stat == 1:
      cmdoptions.append ("--cq-stat")
      cmdoptions.extend (["--cq-stat-output", cqstat_out])
    cmdoptions.extend (["--harnesses", "th_lite"])
    cmdoptions.extend (["--benchmarks", benchmark])
    if uuencode != 1:
      cmdoptions.append ("--no-uuencode")

    implementation  = self.config.getVariable ("EEMBC Implementation")
    if len(implementation) > 0:
      cmdoptions.extend (["--implementation", implementation])

    cmdoptions.extend (["--exec-method", exec_method])
    if exec_method == "datools":
      da = self.getResource("Debug Adapter")
      da_name = da.getAttributeValue ("DA Name")
      cmdoptions.extend (["--da", da_name])
    elif exec_method == "inscript":
      metag_fsim_root        = self.config.getVariable ("METAG_FSIM_ROOT")
      metat_onetest_timeout  = self.config.getVariable ("METAT_ONETEST_TIMEOUT")
      env['METAG_FSIM_ROOT'] = metag_fsim_root
      env['METAT_ONETEST_TIMEOUT'] = metat_onetest_timeout
    if run_as != "":
      cmdoptions.extend (["--run-as", run_as])

    if len(extra) > 0:
      cmdoptions.append ("--")
      cmdoptions.extend (extra)

    cmd.extend(cmdoptions)

    result = self.execute (command=cmd, env=env,
                           workdir="%s/eembc"%workdir)

    pattern = os.path.join(workdir, "eembc", benchmark, "%s%s*.log"%(toolchain,platform))
    for logfile in glob.iglob (pattern):
      os.unlink (logfile)
    if result != 0:
      self.error ("Failed to rebuild log file for EEMBC")

    cmd[0] = "scripts/run.sh"

    result = self.execute (command=cmd, env=env,
                           workdir="%s/eembc"%workdir)

    if result != 0:
      self.error ("Failed to run EEMBC")

    # Now process the results
    cmd = ["scripts/results.sh"]
    cmd.extend(cmdoptions)

    result = self.execute (command=cmd, env=env,
                           workdir="%s/eembc"%workdir)

    if result != 0:
      self.error ("Failed to run EEMBC result script")

    bmarks = self.fetchBmarkList(workdir, platform)
    if bmarks == False:
      # Error set by fetchBmarkList
      return False

    logs = "%s/%s/%s"%(benchmark, toolchain, platform)

    if cq_stat == 1:
      runtime_dict  = self.read_results_runtime ("%s/%s/runtime.txt" %(cqstat_out, logs))
      cctime_dict   = self.read_results_cctime  ("%s/%s/cctime.txt"  %(cqstat_out, logs))
      hosttime_dict = self.read_results_hosttime("%s/%s/hosttime.txt"%(cqstat_out, logs))
      codesize_dict = self.read_results_codesize("%s/%s/codesize.txt"%(cqstat_out, logs))
      test_set  = sets.Set(runtime_dict.keys())
      test_set |= sets.Set(cctime_dict.keys())
      test_set |= sets.Set(hosttime_dict.keys())
      test_set |= sets.Set(codesize_dict.keys())
      test_set |= sets.Set(bmarks)
      for key in test_set:
        results = {}
        test_passed = True
        if key in runtime_dict:
          results['runtime']  = runtime_dict[key]  
        elif key in hosttime_dict:
          test_passed = False
        if key in cctime_dict:
          results['cctime']   = cctime_dict[key]
        if key in hosttime_dict:
          results['hosttime'] = hosttime_dict[key]
        if key in codesize_dict:
          results['codesize'] = codesize_dict[key]

        self.testsuiteSubmit (key, test_passed, extendedresults=results)

      logs_tgz = "%s/%s_%s_%s.tar.gz"%(cqstat_out, benchmark, toolchain, platform)
      tar = tarfile.open (logs_tgz, "w:gz")
      tar.add ("%s/%s"%(cqstat_out, logs), arcname=logs)
      tar.close()
      self.registerLogFile (logs_tgz)

    return True

  def read_results_runtime(self, log):
    dict = {}
    for row in csv.reader(open(log)):
      if row[1] != 'UNKNOWN' and row[1] != 'FAIL':
        dict[row[0]] = float(row[1])
    return dict

  def read_results_cctime(self, log):
    dict = {}
    for row in csv.reader(open(log)):
      time = float(row[2].split(':')[1])
      test = row[0]
      dict[test] = time + (dict[test] if test in dict else 0)
    return dict

  def read_results_hosttime(self, log):
    dict = {}
    for row in csv.reader(open(log)):
      dict[row[0]] = float(row[1].split(':')[1])
    return dict

  def read_results_codesize(self, log):
    dict = {}
    for row in csv.reader(open(log)):
      test = row[0]
      dict[test] = int(row[3]) + (dict[test] if test in dict else 0)
    return dict
