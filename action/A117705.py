import os
from Action import Action
from IMGAction import IMGAction
from common.KernelTest import KernelTest
from Config import CONFIG

# Bullet

class A117705(Action, IMGAction, KernelTest):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117705
    self.name = "Bullet"

  mtests ={"meta": {"normal": {"single":       ["NAME=single_fs_meta",    "BULLETFP=single", "TOOLFP=single", "MINIM=no"],
                               "singledouble": ["NAME=single_fds_meta",   "BULLETFP=single", "TOOLFP=double", "MINIM=no"],
                               "double":       ["NAME=double_fds_meta",   "BULLETFP=double", "TOOLFP=double", "MINIM=no"]},
                    "optimised": {"single":       ["NAME=single_ofs_meta",   "BULLETFP=single", "TOOLFP=optsingle", "MINIM=no"],
                                  "singledouble": ["NAME=single_ofds_meta",  "BULLETFP=single", "TOOLFP=optdouble", "MINIM=no"],
                                  "double":       ["NAME=double_ofds_meta",  "BULLETFP=double", "TOOLFP=optdouble", "MINIM=no"]}},
           "minim": {"optimised": {"single":       ["NAME=single_ofs_minim",  "BULLETFP=single", "TOOLFP=optsingle", "MINIM=yes"],
                                   "singledouble": ["NAME=single_ofds_minim", "BULLETFP=single", "TOOLFP=optdouble", "MINIM=yes"],
                                   "double":       ["NAME=double_ofds_minim", "BULLETFP=double", "TOOLFP=optdouble", "MINIM=yes"]}}}

  atests ={"arm": {"singledouble": ["NAME=single_fds_arm",   "BULLETFP=single", "TOOLFP=double", "THUMB=no"],
                   "double":       ["NAME=double_fds_arm",   "BULLETFP=double", "TOOLFP=double", "THUMB=no"]},
           "thumb": {"singledouble": ["NAME=single_fds_thumb", "BULLETFP=single", "TOOLFP=double", "THUMB=yes"],
                     "double":       ["NAME=double_fds_thumb", "BULLETFP=double", "TOOLFP=double", "THUMB=yes"]}}

  # Execute the action.
  def run(self):
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("KL metag CVSROOT")
#    if not self.ccsCheckout("metag/support/examples/bullet/src.ccs", "Bullet", self.version, cvsroot):
#      self.error("Unable to check out bullet")
    if not self.cvsCheckout("metag/support/examples/bullet", cvsroot):
      self.error("Unable to check out bullet")

    if self.version=="ARM Linux":
      return self.runARM()
    else:
      return self.runMETA()

  def runARM(self):
    isa = self.config.getVariable("Instruction Set")
    fpuconfig = self.config.getVariable("FPU Variant")

    env = {}
    env['PATH'] = CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.cmake), os.environ['PATH']])
    env['INSTALL_DIR'] = self.getSharedPath()

    # Order of toolkits is important as using Linux also requires a GCC embedded
    # toolchain.
    cmd = []
    buildtests = []
    isalist = []
    if isa in ("Any", "ARM"):
      isalist.append("arm")
    if isa in ("Any", "Thumb2"):
      isalist.append("thumb")
    fpulist = []
    if fpuconfig == "Any":
      fpulist.extend(["singledouble", "double"])
    else:
      fpulist.append(fpuconfig)

    for isa in isalist:
      if isa in A117705.atests:
        for fpuconfig in fpulist:
          if fpuconfig in A117705.atests[isa]:
            buildtests.append(A117705.atests[isa][fpuconfig])

    # Build with META Embedded GCC
    env['ARM_INST_ROOT'] = self.config.getVariable("ARM_INST_ROOT")
    cmd=["make", "-f", "Makefile.ARM", "all-linux"]

    bulletdir = os.path.join(self.getWorkPath(), "metag", "support", "examples", "bullet")
    for test in buildtests:
      command = cmd[:]
      command.extend(test)
      if self.execute(command=command, env=env, workdir=bulletdir) != 0:
        self.error("Failed to build test: %s" % test)
    return self.success()

  def runMETA(self):
    isa = self.config.getVariable("Instruction Set")
    optfp = self.config.getVariable("Optimised Math")
    fpuconfig = self.config.getVariable("FPU Variant")

    env = {}
    env['PATH'] = CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.cmake), os.environ['PATH']])
    env['OPTFPPATH'] = self.testrun.getSharedPath("FPU Math Library")
    env['INSTALL_DIR'] = self.getSharedPath()

    # Order of toolkits is important as using Linux also requires a GCC embedded
    # toolchain.
    cmd = []
    buildtests = []
    isalist = []
    if isa in ("Any", "meta"):
      isalist.append("meta")
    if isa in ("Any", "minim") and \
       self.testrun.getVersion("META Linux Buildroot") == None:
      isalist.append("minim")
    optfplist = []
    if optfp in ("Any", "optimised"):
      optfplist.append("optimised")
    if optfp in ("Any", "normal"):
      optfplist.append("normal")
    fpulist = []
    if fpuconfig == "Any":
      fpulist.extend(["single", "singledouble", "double"])
    else:
      fpulist.append(fpuconfig)

    for isa in isalist:
      if isa in A117705.mtests:
        for optfp in optfplist:
          if optfp in A117705.mtests[isa]:
            for fpuconfig in fpulist:
              if fpuconfig in A117705.mtests[isa][optfp]:
                buildtests.append(A117705.mtests[isa][optfp][fpuconfig])

    if self.testrun.getVersion("META Linux Buildroot") != None:
      # Build with META Linux GCC
      self.initialiseBuildSystem()
      env['METAG_LINUX_ROOT'] = self.toolkit_path
      cmd=["make", "-f", "Makefile.META", "all-linux"]
    elif self.testrun.getVersion("MetaMtxToolkit") != None:
      # Build with META Embedded GCC
      env['METAG_INST_ROOT'] = self.config.getVariable("METAG_INST_ROOT")
      cmd=["make", "-f", "Makefile.META", "all-embedded"]
    else:
      self.error("Unable to determine what toolchain to build with")

    bulletdir = os.path.join(self.getWorkPath(), "metag", "support", "examples", "bullet")
    for test in buildtests:
      command = cmd[:]
      command.extend(test)
      if self.execute(command=command, env=env, workdir=bulletdir) != 0:
        self.error("Failed to build test: %s" % test)
    return self.success()

