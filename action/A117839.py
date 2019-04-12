import os
from Action import Action
from Config import CONFIG
from OvertestExceptions import ConfigException
from parsers.GCC4Regression import GCC4RegressionParser
import re
import glob

# GNU LD Test

class A117839(Action, GCC4RegressionParser):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117839
    self.name = "GNU LD Test"

  # Execute the action.
  def run(self):
    binutils = os.path.join(self.testrun.getSharedPath("Binutils"), "binutils")
    dejagnu = os.path.join(self.testrun.getSharedPath("Dejagnu"), "dejagnu")
    triple = self.config.getVariable("Triple")

    # Create the site config to run the suite
    self.make_site(binutils, triple)

    toolchain_root = self.config.getVariable("Toolchain Root")

    env = {}
    env['PATH'] = CONFIG.makeSearchPath([os.path.join(toolchain_root, "bin"),
					dejagnu, os.environ['PATH']])
    env['LC_ALL'] = 'C'

    try:
      arch = self.config.getVariable("Architecture")
    except ConfigException, e:
      arch = "mips"

    target_board = arch + "-sim-mti32"
    cmd = ["runtest", "--tool", "ld", "--target_board=%s" % target_board]
    self.execute(env=env, command=cmd)
    self.registerLogFile(os.path.join (self.getWorkPath(), "ld.log"), compress=True)
    self.registerLogFile(os.path.join (self.getWorkPath(), "ld.sum"), compress=True)
    summary = self.parse (os.path.join (self.getWorkPath(), "ld.log"))
    return self.success(summary)

  def make_site(self, src, triple):
    a = """set host_triplet x86_64-pc-linux-gnu
	   set target_alias %s
	   set target_triplet %s
	   set build_triplet x86_64-pc-linux-gnu
	   set srcdir %s/ld/testsuite
	   set objdir %s
	   set AS %s-as
	   set OBJDUMP %s-objdump
	   set OBJCOPY %s-objcopy
	   set READELF %s-readelf
	   set NM %s-nm
	   set LD %s-ld
	   set ADDR2LINE %s-addr2line"""
    if triple.endswith("elf"):
      a = a + """
		 set CC skip-cc
		 set CXX skip-cxx"""

    canon_triple = triple
    if triple.startswith("nanomips"):
      canon_triple = triple.replace("nanomips-", "nanomips-unknown-")
    a = a % (triple, canon_triple, src, self.getWorkPath(), triple,
             triple, triple, triple, triple, triple, triple)
    with open(os.path.join(self.getWorkPath(), "site.exp"), "w") as fh:
      fh.write(a)
