import os
from Action import Action
from Config import CONFIG
from parsers.GCC4Regression import GCC4RegressionParser

# GDB Test

class A117836(Action, GCC4RegressionParser):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117836
    self.name = "GDB Test"

  # Execute the action.
  def run(self):
    gdb = os.path.join(self.testrun.getSharedPath("GDB"), "gdb")
    dejagnu = os.path.join(self.testrun.getSharedPath("Dejagnu"), "dejagnu")
    triple = self.config.getVariable("Triple")

    # Create the site config to run the suite
    self.make_site(gdb, triple)

    toolchain_root = self.config.getVariable("Toolchain Root")
    
    env = {}
    env['PATH'] = CONFIG.makeSearchPath([os.path.join(toolchain_root, "bin"),
		                        "/user/rgi_data2/Verify/CentOS-5/Tcl_8.6.4_x64/root/bin",
					dejagnu, os.environ['PATH']])
    if triple == "nanomips-elf" and self.version == "GNUSIM":
      target_board = "nanomips-sim-mti32"
      gdb_bin = os.path.join(toolchain_root, "bin", "%s-gdb" % triple)
    else:
      self.error("Unknown configuration")

    cmd = ["runtest", "--target_board=%s" % target_board, "GDB=%s" % gdb_bin]
    self.execute(env=env, command=cmd)

    self.registerLogFile(os.path.join (self.getWorkPath(), "gdb.log"), compress=True)
    self.registerLogFile(os.path.join (self.getWorkPath(), "gdb.sum"), compress=True)

    summary = self.parse (os.path.join (self.getWorkPath(), "gdb.log"))

    return self.success(summary)

  def make_site(self, gdb_src, triple):
    a = """set host_triplet x86_64-pc-linux-gnu
	   set target_alias %s
	   set target_triplet %s
	   set build_triplet x86_64-pc-linux-gnu
	   set srcdir %s/gdb/testsuite
	   set tool gdb
	   source ${srcdir}/lib/append_gdb_boards_dir.exp"""

    canon_triple = triple
    if triple == "nanomips-elf":
      canon_triple = "nanomips-unknown-elf"
    a = a % (triple,canon_triple,gdb_src)
    with open(os.path.join(self.getWorkPath(), "site.exp"), "w") as fh:
      fh.write(a)
