import os
from Action import Action
import sys

# Build EEMBC

class A108989(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108989
    self.name = "Build EEMBC"

  # Execute the action.
  def run(self):
    host = self.getResource ("Execution Host")
    eembc_root = host.getAttributeValue ("EEMBC Root")

    METAG_INST_ROOT = self.config.getVariable ("METAG_INST_ROOT")
    imgpath = os.path.join(sys.path[0], "share", "img")

    self.config.setVariable("EEMBC Workspace", self.getWorkPath())

    env = {}
    env['METAG_INST_ROOT'] = METAG_INST_ROOT
    env['EXTRA_CFLAGS_OVERRIDE'] = self.config.getVariable ("Compiler Flags")
    env['EXTRA_LDLKFLAGS'] = "-mminim"

    # Execute an arbitrary command overriding some environment variables
    result = self.execute(env=env, workdir=eembc_root, \
                                   command=["make", "TOOLCHAIN=metagcc", \
                                                    "WORKSPACE=%s/"%self.getWorkPath(), \
                                                    "CACHE_IMG=%s"%os.path.join(imgpath, "214_32m_ldlk.img"), \
                                                    "BOARD_IMG=%s"%os.path.join(imgpath, "214_32m_mem.img"), \
                                                    "CQSTATS=1", \
                                                    "ALL_TARGETS=mkdir targets", \
                                                    "all-lite", "cleanlogs"])

    self.execute(env=env, command=["tar", "-czf", "metagcc.tgz", "metagcc"])
    self.execute(env=env, command=["rm", "-rf", "metagcc"])

    return (result == 0)
