#  Copyright (C) 2012-2020 MIPS Tech LLC
#  Written by Matthew Fortune <matthew.fortune@imgtec.com> and
#  Daniel Sanders <daniel.sanders@imgtec.com>
#  This file is part of Overtest.
#
#  Overtest is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3, or (at your option)
#  any later version.
#
#  Overtest is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with overtest; see the file COPYING.  If not, write to the Free
#  Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
#  02110-1301, USA.
import os
from Config import CONFIG
from utils.Utilities import versionCompare
import types
import urlparse

class IMGAction:
  """
  Generic functionality available within IMG. 
  """
  debug_verbose = 0

  def __init__(self):
    """
    Set up the IMGAction class
    """

  def cvsCheckout(self, module, cvsroot, tag="HEAD", workdir=None):
    """
    Check out files from a CVS repository

    :param module: CVS module to check out
    :type module: path
    :param cvsroot: The repository to use
    :type cvsroot: string
    :param tag: CVS tag to use (default 'HEAD')
    :type tag: string
    :param workdir: The location to check out in to (default is working area)
    :type workdir: path
    :return: success or failure as indicated by cvs exit code
    :rtype: boolean
    """
    return self.execute(workdir=workdir, env={"CVSROOT":cvsroot}, command=[CONFIG.cvs, "co", "-r", tag, module]) == 0

  def ccsCheckout(self, componentfile, component, version, cvsroot, workdir=None):
    """
    Check out files from a repository using the CCS command

    :param componentfile: Specifies the CCS component file defining the
                          component
    :type componentfile: path
    :param component: Specifies the CCS component name to retrieve
    :type component: string
    :param version: Specifies the CCS component version
    :type version: string
    :param cvsroot: The repository to use
    :type cvsroot: string
    :param workdir: The location to check out in to (default is working area)
    :type workdir: path
    :return: success or failure as indicated by ccs exit code
    :rtype: boolean
    """
    return self.execute(workdir=workdir, env={"CVSROOT":cvsroot}, command=[CONFIG.ccs, "-c", componentfile, "checkout", component+":"+version]) == 0

  def setNeoLocale(self, env):
    """
    Updates the specified environment with the current NEOLOCALE. The
    environment is modified in place.

    :param env: A partial environment
    :type env: dictionary
    :return: The updated environment
    :rtype: dictionary
    """
    host = self.getResource("Execution Host")
    locale = host.getAttributeValue("Neo Locale")
    env['NEOLOCALE'] = locale
    return env

  def neoVerify(self, what=None, CAT=None, TARGET=None, VERIFY=None, TOOLS=None, FSIM=None, SUBTARGETS=None, PICK=None, META2_CONFIG=None, PYTHON=None, GROUP=None, env=None, MATRIX=None, PUB=None, FPGA_CONFIG=None, COMPILER=None, MINIM=None, JUSTONE=None, EXTRA=None, template=None):
    """
    Run the verify script using the neo utility.

    :param what: Specifies the sub-command i.e. 'select' or 'publish'
    :type what: string
    :param CAT: Specifies the category of tests i.e. 'mtx' or 'meta2'
    :type CAT: string
    :param TARGET: Specifies the core to run on i.e. 'MTXC122' or 'any'
    :type TARGET: string
    :param VERIFY: Specifies the version of the VerifyToolkit component to use.
                   This will default to the version of the action in the testrun
    :type VERIFY: string
    :param TOOLS: Specifies the version of the MetaMtxToolkit component to use.
                  This will default to the version of the action in the testrun.
    :type TOOLS: string
    :param FSIM: Specifies the version of the MetaMtxCoreSim component to use.
                 This will default to the version of the action in the testrun.
    :type FSIM: string
    :param SUBTARGETS: The implementation or area of the target such as 'fpga'
                       or 'msub'
    :type SUBTARGETS: string
    :param PYTHON: Specifies the version of Python to use, it must be present in
                   the Verify are for the specific platform neo verify will run
                   on.
    :type PYTHON: string
    :type COMPILER: string
    :param COMPILER: Specify the compiler
    :type JUSTONE: string
    :param JUSTONE: Specify the test to run
    :type command: string
    :param command: Specify the Verify-like command to run
    """
    if env == None:
      env = {}

    self.setNeoLocale(env)

    if VERIFY == None:
      VERIFY = self.testrun.getVersion ("VerifyToolkit")
    
    if FSIM == None:
      simulator_spec =  self.config.getVariable ("Simulator Spec")
      FSIM = simulator_spec

      if simulator_spec == "scratch":
        env['METAG_FSIM_ROOT'] = self.config.getVariable("METAG_FSIM_ROOT")

    if TOOLS == None:
      toolkit_spec =  self.config.getVariable ("Toolkit Spec")
  
      if toolkit_spec == "scratch":
        TOOLS = "scratch"
        env['METAG_INST_ROOT'] = self.config.getVariable ("METAG_INST_ROOT")
      else:
        TOOLS = toolkit_spec

    command = [CONFIG.neo]
    if what != None:
      command.append("verify")
      command.append(what)
    else:
      command.append(template)
    if CAT != None:
      command.append("CAT=%s"%CAT)
    if TARGET != None:
      command.append("TARGET=%s"%TARGET)
    if VERIFY != None:
      command.append("VERIFY=%s"%VERIFY)
    if TOOLS != None:
      command.append("TOOLS=%s"%TOOLS)
    if FSIM != None:
      command.append("FSIM=%s"%FSIM)
    if SUBTARGETS != None:
      command.append("SUBTARGETS=%s"%SUBTARGETS)
    if PYTHON != None:
      command.append("PYTHON=%s"%PYTHON)
    if PICK != None:
      command.append("PICK=%s"%PICK)
    if META2_CONFIG != None:
      command.append("META2_CONFIG=%s"%META2_CONFIG)
    if GROUP != None:
      command.append("GROUP=%s"%GROUP)
    if FPGA_CONFIG != None:
      command.append("FPGA_CONFIG=%s"%FPGA_CONFIG)
    if MATRIX != None and MATRIX != "":
      command.append("MATRIX=%s"%MATRIX)
    if PUB != None:
      command.append("PUB=%s"%PUB)
    if MINIM != None:
      command.append("MINIM=%s"%MINIM)
    command.append("MATRIX_TIDY=1")
    if COMPILER != None:
      env['COMPILER'] = COMPILER
    if JUSTONE != None and JUSTONE != "":
      command.append("JUSTONE=%s"%JUSTONE)
    if EXTRA != None:
      command.extend(EXTRA)
    if not 'METACLIB' in env:
      env['METACLIB'] = "newlib"
    return self.execute (command=command, env=env)

  def neoRunall(self, VERIFY, PUB, script, keys=None):
    """
    Run the tests in PUB using the version of the verify suite specified
    targets are assumed to be available
    """
    env = {}
    self.setNeoLocale(env)

    if keys == None:
      keys = {}
    da = self.getResource("Debug Adapter")
    da_name = da.getAttributeValue("DA Name")
    board = self.getResource("Target Board")
    fpga_type = board.getAttributeValue("FPGA Type")
    env['DA_NAME'] = da_name
    env['TARGET_FPGA_TYPE'] = fpga_type

    command = [CONFIG.neo, script, "PUB=%s" % PUB]
    if script == "python_runall":
      command.append("VERIFY=%s" % VERIFY)

    command.append("DONOTCLAIM")

    ret = self.execute(command=command, env=env)

    try:
      passed = open(os.path.join (self.getWorkPath (), ".runall_passed"), "r")
      pass_list = passed.read().split()
      passed.close()
      for test in pass_list:
        if test in keys:
          self.testsuiteSubmit(test, True, version=keys[test])
        else:
          self.testsuiteSubmit(test, True)
    except IOError:
      None

    try:
      failed = open(os.path.join (self.getWorkPath (), ".runall_failed"), "r")
      fail_list = failed.read().split()
      failed.close()
      for test in fail_list:
        if test in keys:
          self.testsuiteSubmit(test, False, version=keys[test])
        else:
          self.testsuiteSubmit(test, False)
    except IOError:
      None

    self.registerLogFile (os.path.join (self.getWorkPath (), ".runall_passed"))
    self.registerLogFile (os.path.join (self.getWorkPath (), ".runall_failed"))
    self.registerLogFile (os.path.join (self.getWorkPath (), ".runall.txt"))

    return (ret in [0,1])

  def neoPatchToolkit (self, toolkit_spec, toolkit_version, toolkit_variant, tool, tool_version, target_library = False):
    """
    Create or patch an existing toolkit root with the specified tool
    """
    env = {}
    self.setNeoLocale(env)

    tool_root = "root"
    if target_library:
      version_parts = toolkit_version.split(".")
      if len(version_parts) < 4:
        self.error("Can't determine toolkit version for target library")
      if versionCompare(version_parts, ["2", "5", "1"]) >= 0:
        tool_root = "root.%s.%s.%s" % (version_parts[0],version_parts[1],version_parts[2])
      else:
        tool_root = "root.%s.%s.%sb%s" % (version_parts[0],version_parts[1],version_parts[2],version_parts[3])

    tool_build = self.config.getVariable("%s Build" % tool)
    if tool_build == "Any":
      # When no specific tool variant is requested use the toolkit one is specified
      if toolkit_variant == None:
        tool_spec = "%s/%s" % (tool_version, tool_root)
      else:
        tool_spec = "%s:%s/%s" % (tool_version, toolkit_variant, tool_root)
    else:
      tool_spec = "%s:%s/%s" % (tool_version, tool_build.split()[-1], tool_root)

    command = [CONFIG.neo, "patch_toolkit", "MetaMtxToolkit", \
              toolkit_spec, tool, tool_spec]
    ret = self.execute (command=command, env=env)

    if ret != 0:
      self.error ("Failed to patch toolkit %s with %s %s"%(toolkit_spec,tool,tool_spec))

    return True

  def neoIdent (self):
    """
    Get the neo didentstr ident string for this platform
    """
    env = {}
    self.setNeoLocale(env)

    command = [CONFIG.neo, "didentstr"]
    ret = self.execute (command=command, env=env)

    if ret == 0:
      return self.fetchOutput().strip().rstrip("\n")
    else:
      return "[FAILED TO GET IDENT]"

  def neoKeyMaker (self, tgz, style, info_on=0):
    """
    Get the neo didentstr ident string for this platform
    """
    env={}
    self.setNeoLocale(env)
    env['IMGINFO'] = "%d"%info_on
    command = [CONFIG.neo, "keymaker", tgz, "STYLE=%s"%style]
    ret = self.execute (command=command, env=env)
    if ret == 0:
      key = self.fetchOutput().strip().rstrip("\n")
      self.proccount -= 1
      return key
    else:
      self.proccount -= 1
      return None

  def neoMetagInstRoot (self, toolkit_spec):
    """
    Get the METAG_INST_ROOT for the given version of the MetaMtxToolkit
    """
    return self.neoSelect("MetaMtxToolkit", select_spec=toolkit_spec)

  def neoSelect (self, component, version=None, variant=None, root="root", select_spec=None):
    env = {}
    self.setNeoLocale(env)

    if select_spec != None:
      spec = select_spec
    else:
      spec = "%s/%s"%(version,root)
      if variant != None:
        spec = "%s:%s/%s"%(version, variant, root)

    command = [CONFIG.neo, "select", component, spec]
    ret = self.execute(command, env=env)

    if ret == 0:
      return self.fetchOutput().rstrip().split("\n")[-1].split("=")[1]
    else:
      return None

  def neoGetSource (self, workdir, component, version, env=None):
    """
    Fetch some source from neo and place it in workdir
    """
    if env is None:
      env = {}
    self.setNeoLocale(env)

    command = [CONFIG.neo, "get_source", component, version]
    return (self.execute (command=command, workdir=workdir, env=env) == 0)

  def neoNewDist (self, component, version, dist_file):
    """
    Submit the specified dist file to neo
    """
    env = {}
    self.setNeoLocale(env)

    command = [CONFIG.neo, 'new_dist', component, version, dist_file]
    return (self.execute (command=command, env=env) == 0)

  def neoRunDAScript (self, scriptname, args, workdir=None):
    """
    Run the named DAScript
    """
    command = [CONFIG.neo, 'run_dascript', scriptname]

    if type(args) != types.ListType:
      self.error("neoRunDAScript requires a list as the args parameter")

    command.extend(args)

    return self.execute (command=command, workdir=workdir)

  def selectDA (self, DAScriptName):
    """
    Select just the DA specified
    """
    self.execute (command=[CONFIG.daconf, "disableall"])

    ret = self.execute (command=[CONFIG.daconf, "-n", "add", DAScriptName])
    if ret != 0:
      self.error ("DAConf failed to add target. Error code: %u" % ret)

    ret = self.execute (command=[CONFIG.daconf, "-n", "enable", DAScriptName])
    if ret != 0:
      self.error ("DAConf failed to enable target. Error code: %u" % ret)

    return True

  def gitExport(self, uri, tag="master", workdir=None):
    """
    Export files from a git repository

    :param uri: git module to export
    :type uri: uri
    :param tag: git tag to use (default 'master')
    :type tag: string
    :param workdir: The location to export to (default is working area)
    :type workdir: path
    :return: success or failure as indicated by git exit code
    :rtype: boolean
    """
    module_path = urlparse.urlparse(uri).path
    module_name = module_path.split("/")[-1]
    if module_name.endswith(".git"):
      module_name = module_name[:-4]

    ret = self.execute(workdir=workdir, command=[CONFIG.git, "archive", "--format=tar", "--prefix=%s/" % module_name, "--remote=%s" % uri, "--output=%s.tar" % module_name, tag])
    if ret != 0:
      self.error ("git archive failed to export module: %u" % ret)

    ret = self.execute(workdir=workdir, command=["tar", "xf", "%s.tar" % module_name])
    if ret != 0:
      self.error ("tar failed to extract archive: %u" % ret)

    ret = self.execute(workdir=workdir, command=["rm", "%s.tar" % module_name])
    if ret != 0:
      self.error ("rm failed to delete archive: %u" % ret)

    return True
