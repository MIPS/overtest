import os
import sys
from Action import Action
from IMGAction import IMGAction
from OvertestExceptions import *

# Run EEMBC

class A108990(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108990
    self.name = "Run EEMBC"

  # Execute the action.
  def run(self):
    host = self.getResource ("Execution Host")
    eembc_root = host.getAttributeValue ("EEMBC Root")

    METAG_INST_ROOT = self.config.getVariable ("METAG_INST_ROOT")
    imgpath = os.path.join(sys.path[0], "share", "img")

    workspace = self.config.getVariable("EEMBC Workspace")

    self.execute(workdir=workspace, command=["tar", "-xzf", "metagcc.tgz"])
    self.execute(workdir=os.path.join(workspace, "metagcc", "results_lite"), command=["rm -f *"], shell=True)
    self.execute(workdir=os.path.join(workspace, "metagcc", "bin_lite"), command=["rm -f *"], shell=True)

    env = {}
    env['METAG_INST_ROOT'] = METAG_INST_ROOT

    mmetac_cflag = ""
    if self.version.endswith(".sim"):
      # We are going to use the linux simulator
      env['METAG_FSIM_ROOT'] = self.config.getVariable ("METAG_FSIM_ROOT")
      # WORK NEEDED: Deprecate this
      env['FSIM_INST_ROOT'] = env['METAG_FSIM_ROOT']
      env['METAG_SIM'] = self.config.getVariable ("Simulator Config");
      core = env['METAG_SIM']
      if core == "122":
        mmetac_cflag = "-mmetac=1.2"
      else:
        env['EXTRA_LDLKFLAGS'] = "-mminim"

    else:
      # Find out about the DA that has been allocated
      da = self.getResource ("Debug Adapter")
      env['DA_NAME'] = da.getAttributeValue ("DA Name")

      board = self.getResource ("Target Board")
      cores = board.getAttributeValues ("Core Revision")

      if len(cores) == 1:
        core = cores[0]
      else:
        core = board.getRequestedAttributeValue ("Core Revision")

      if core == "META122":
        core = "122"
        mmetac_cflag = "-mmetac=1.2"
      elif core == "META2" or core == "COMET":
        core = "214"
        mmetac_cflag = "-mmetac=2.1"
        env['EXTRA_LDLKFLAGS'] = "-mminim"
      elif core == "Meta 2 (213)":
        core = "213"
        mmetac_cflag = "-mmetac=2.1"
        env['EXTRA_LDLKFLAGS'] = "-mminim"
      else:
        raise ResourceException("Unknown core found: %s"%core)

    board = "BOARD_IMG=%s"%os.path.join(imgpath, "%s_%s_mem.img"%(core, "32m"))
    cache = "CACHE_IMG=%s"%os.path.join(imgpath, "%s_%s_ldlk.img"%(core, "32m"))

    env['EXTRA_CFLAGS_OVERRIDE'] = "%s %s" % (self.config.getVariable ("Compiler Flags"), mmetac_cflag)
    env['EXTRA_LDFLAGS'] = env['EXTRA_CFLAGS_OVERRIDE']

    result = self.execute(env=env, workdir=eembc_root, \
                                   command=["make", "TOOLCHAIN=metagcc", \
                                                    "WORKSPACE=%s/"%workspace, \
                                                    cache, \
                                                    board, \
                                                    "CQSTATS=1", \
                                                    "CQPUBLISHDIR=%s"%os.path.join(self.getWorkPath(),"publish"), \
                                                    "ALL_TARGETS=cqpublish", \
                                                    "all-lite"])
    success = (result == 0)

    self.execute(command=["tar", "-czf", os.path.join(self.getWorkPath(),"publish.tgz"),\
                          "publish"])

    self.execute(workdir=workspace, command=["rm", "-rf", "metagcc"])
    
    self.registerLogFile(os.path.join(self.getWorkPath(),"publish.tgz"))

    return success

