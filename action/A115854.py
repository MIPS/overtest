import hashlib
import re
import os
import glob
import shlex
from Config import CONFIG
from utils.Utilities import versionCompare
from Action import Action
from IMGAction import IMGAction

# Build

def md5_for_file(f, block_size=2**20):
  md5 = hashlib.md5()
  while True:
    data = f.read(block_size)
    if not data:
      break
    md5.update(data)
  return md5.hexdigest()

class A115854(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 115854
    self.name = "Build"

  # Execute the action.
  def run(self):
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
      self.error("Unknown Target Board cannot determine implementation")

    if target_board == "214_4t2df FPGA":
      platform_family = "214_4t2df"
    elif "COMET" in target_board:
      platform_family = "comet"
    elif target_board == "Chorus 2 Metamorph":
      platform_family = "fimber"
    else:
      self.error("Unknown Target Board cannot determine platform family")

    config          = self.config.getVariable ("RA Config %s"%platform_family)
    do_apps         = self.config.getVariable ("RA Do Apps")
    xcflags         = self.config.getVariable ("RA XCFLAGS")
    self.config.setVariable ("RA Config", config)

    xcflags = xcflags if xcflags != "" else None

    env = { 'METAG_INST_ROOT' : metag_inst_root,
            'ALLOW_REMOTE_HASP' : '1',
            'METAGS_DIR' : "%s/metags-dir" % workdir,
            'PATH' : CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo),
                                            CONFIG.getProgramDir(CONFIG.perl),
                                            os.environ['PATH']])
          } 

    try:
      os.makedirs (env['METAGS_DIR'])
    except OSError:
      pass

    toolchain_version = self.testrun.getVersion("MetaMtxToolkit")

    if self.testrun.getVersion("MECCToolkit") != None:
      mecc_inst_root = self.config.getVariable ("MECC_INST_ROOT")
      env['MECC_INST_ROOT'] = mecc_inst_root
      env['LM_LICENSE_FILE'] = os.path.join(os.path.expanduser("~"), "licenses", "uncounted.lic")
      toolchain = "mecc"
      toolchain_version = self.testrun.getVersion("MECCToolkit")

    cmd = ["./main.pl"]
    cmd.extend (["--stage=build"])
    cmd.extend (["--compiler=%s" % toolchain])
    cmd.extend (["--compiler-version=%s" % toolchain_version])
    cmd.extend (["--config=%s" % config])
    cmd.extend (["--implementation=%s" % implementation])
    if xcflags != None:
      cmd.extend (["--xcf=%s" % xcflags])
    xlflags = self.config.getVariable ("RA XLFLAGS")
    if xlflags != "":
      cmd.extend (["--xlf=%s" % xlflags])

    xiflags = self.config.getVariable ("RA XIFLAGS")
    if xiflags != "":
      cmd.extend (["--xif=%s" % xiflags])

    arbitrary = self.config.getVariable ("RA Arbitrary")

    if arbitrary != "":
      varlist = shlex.split (str(arbitrary))
      for envvar in varlist:
        envvar = envvar.split("=", 1)
        if envvar[0] in env:
          self.error ("Unable to override pre-set environment variable: %s" % envvar)
        if len(envvar) == 1:
          env[envvar[0]] = "1"
        else:
          env[envvar[0]] = envvar[1]

    cmd.extend (do_apps.split(','))

    result = self.execute (command=cmd, env=env,
                           workdir=workdir)

    # Exit code 2 says something worked
    if result != 0 and result != 2:
      self.error ("Failed to build RA")

    # New versions of the regression apps can be interrogated to find out
    # what should have been built and where
    cmd[1] = "--stage=list";

    result = self.execute (command=cmd, env=env,
                         workdir=workdir)

    # Exit code 2 says something worked
    if result != 0 and result != 2:
      self.error ("Failed to get list of apps")
  
    listing = self.fetchOutput()
    tests = {}
    for line in listing.strip().split("\n"):
      testinfo = line.strip().split(" ")
      tests[testinfo[0]] = testinfo[1:]

    staging = os.path.join (workdir, "staging", "compile", "app");
    for test in tests:
      test_dir = os.path.join (staging, tests[test][0], test)
      test_ldlk = tests[test][1]
      threads = tests[test][2:]
      passed = True
      results = {}

      for thread in threads:
        lds_bin = os.path.join (test_dir, "test%ss.elf" % (thread))
        if os.path.exists (lds_bin):
          results['LD-SL_T0 MD5'] = md5_for_file (open(lds_bin))
        else:
          passed = False

        ld_bin = os.path.join (test_dir, "test%s.elf" % (thread))
        if os.path.exists (ld_bin):
          results['LD_T0 MD5'] = md5_for_file (open(ld_bin))

        ldlk_bin = os.path.join (test_dir, "%s_t%s.elf" % (test_ldlk, thread))
        if os.path.exists (ldlk_bin):
          results['LDLK_T0 MD5'] = md5_for_file (open(ldlk_bin))
	  
      self.testsuiteSubmit (test, passed, extendedresults=results)

    return True
