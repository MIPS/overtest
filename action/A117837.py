import os
from Action import Action
from Config import CONFIG
from OvertestExceptions import ConfigException
import re
import glob


# GOLD Test

class A117837(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117837
    self.name = "GOLD Test"

  # Execute the action.
  def run(self):
    triple = self.config.getVariable("Triple")
    toolchain_root = self.config.getVariable("Toolchain Root")
    # Execute a command overriding some environment variables
    result = self.execute(command=[CONFIG.git, "clone",
					       "--reference=/projects/mipssw/git/mips_tool_chain.git",
					       "--branch=master",
					       "git://dmz-portal.mipstec.com/mips_tool_chain.git",
					       "mips_tool_chain"])
    if result != 0:
      self.error("Unable to clone repository")

    # Now construct the work area
    result = self.execute(command=["build_scripts/make_workarea %s %s" % (self.getWorkPath(), "git://dmz-portal.mipstec.com")],
			  workdir=os.path.join(self.getWorkPath(), "mips_tool_chain"),
			  shell=True)
    if result != 0:
      self.error("Unable to make work area")

    result = self.execute(command=[CONFIG.git, "checkout", "master"],
			  workdir=os.path.join(self.getWorkPath(), "src", "mips_tool_chain"))

    if result != 0:
      self.error("Unable to change branch")

    result = self.execute(workdir=os.path.join(self.getWorkPath(), "src", "mips_tool_chain"),
	                  command=[CONFIG.git, "rev-parse", "HEAD"])
    if result == 0:
      self.config.setVariable("Toolchain Build rev", self.fetchOutput().strip())

    target = self.config.getVariable("Triple")

    build = os.path.join(self.getWorkPath(), "obj-%s" % target)
    install = "/none/"

    # Add in the path of any host compiler specified
    try:
      host_triple = self.config.getVariable("Host Triple")
      if host_triple != "":
	host_version = self.config.getVariable("Host Version")
	host_bin = "/projects/mipssw/toolchains/%s/%s/bin" % (host_triple, host_version)
	host_path = host_bin
    except ConfigException, e:
      host_triple = ""
      host_path = ""
      pass


    # Prepare for main tools build
    options = ["--path=%s" % host_path,
	       "--git_home=ssh://gitosis@dmz-portal.mips.com",
	       "--build=%s" % build,
	       "--prefix=%s" % install,
	       "--target=%s" % target,
	       "--jobs=%d" % self.concurrency]

    # Set the host tools if specified
    if host_triple != "":
      options.append("--host=%s" % host_triple)
      # For linux hosted builds we expect the newly built tools to execute on
      # the current distro as the C library used should be older than the
      # native one.  We do this by forcing the build and host to match.
      if "pc-linux-gnu" in host_triple:
        options.append("--build_triple=%s" % host_triple)

    # Gather the location of all the packages
    gold = os.path.join(self.testrun.getSharedPath("GOLD"), "gold")
    options.append("--src=gold:%s" % gold)

    # Build GOLD
    cmd = ["b/build_toolchain", "build"]
    cmd.extend(options)

    if self.execute(command=[" ".join(cmd + ["gold", "--make_target_install=skip"])],
		    shell=True) != 0:
      self.error("Failed to build gold")

    env = {}
    env['PATH'] = CONFIG.makeSearchPath([os.path.join(toolchain_root, "bin"),
					 host_path,
					 os.environ['PATH']])

    cmd = ["make", "TEST_READELF=%s-readelf" % triple,
	   "TEST_OBJDUMP=%s-objdump" % triple,
	   "TEST_OBJCOPY=%s-objcopy" % triple,
	   "TEST_STRIP=%s-strip" % triple,
	   "TEST_AR=%s-ar" % triple,
	   "TEST_NM=%s-nm" % triple,
	   "TEST_AS=%s-as" % triple, "check"]

    testsuite_path = os.path.join (build, "gold", "gold", "testsuite")
    self.execute(env=env, command=cmd,
		 workdir=testsuite_path)

    logfile = os.path.join (testsuite_path, "test-suite.log")
    self.registerLogFile(logfile)
    results = {}
    with open(logfile, "r") as fh:
      for line in fh:
	# 1 of 12 tests failed.
	if "tests failed" in line:
	  parts = line.split(" ")
	  results["FAIL"] = int(parts[0])
	  results["PASS"] = int(parts[2])
	# All 12 tests passed.
	elif "tests passed" in line:
	  parts = line.split(" ")
	  results["PASS"] = int(parts[1])

    return self.success(results)


