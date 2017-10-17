import os
from Action import Action
from IMGAction import IMGAction
from common.Dejagnu import DejagnuCommon
from parsers.GCC4Regression import GCC4RegressionParser

# Libstdc++-v3 Regression Suite

class A108988(Action, IMGAction, DejagnuCommon, GCC4RegressionParser):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108988
    self.name = "Libstdc++-v3 Regression Suite"

  # Execute the action.
  def run (self):
    testsuiteSource = os.path.join (self.getWorkPath(), "source")
    testsuiteResults = os.path.join (self.getWorkPath(), "results")

    # Get the testsuite source
    result = self.neoGetSource (testsuiteSource, "Gcc2Libstdc++Testsuite",
                                                 self.testrun.getVersion ("Gcc2Libstdc++Testsuite"))
    if not result:
      self.error ("Failed to fetch testsuite source")

    # Determine the CPU from the version string
    cpu = self.getCPU ()

    # Create the correct environment based on the version string, variables and resources
    env = {}
    env = self.setupDejagnuEnvironment (env, testsuiteSource, cpu)

    # Find and format compiler flags for dejagnu
    cflags = self.getDejagnuCflags ()

    # Get the location of the testsuite
    libstdcppPath = os.path.join (testsuiteSource, "metag", "tools", "gcc2", "libstdc++-v3")

    # Write a site.exp file for libstdc++-v3
    site_exp = ("set tmpdir \"%s\"\n"+\
                "set objdir \".\"\n"+\
                "set srcdir \"%s/testsuite/\"\n"+\
                "set target_alias \"%sg-local\"\n"+\
                "set libiconv \"\"\n"+\
                "set baseline_file \"%s/config/abi/post//baseline_symbols.txt\"") % \
               (self.getWorkPath(), libstdcppPath, cpu, libstdcppPath)

    try:
      if not os.path.exists(testsuiteResults):
        os.mkdir (testsuiteResults)
      f = open(os.path.join (testsuiteResults, "site.exp"), "w")
      f.write(site_exp)
      f.close()
    except IOError:
      self.error("Failed to write site.exp")

    # Find the corba harness
    cpu_local_run = "%sg-local-run" % cpu

    # Add the compiler into the search path
    if not 'PATH' in env:
      env['PATH'] = os.environ['PATH']
    env['PATH'] = "%s:%s" % (os.path.join(env['METAG_INST_ROOT'], "bin"), env['PATH'])

    # Run the testsuite
    result = self.execute(env=env, workdir=testsuiteResults,
                                   command=["runtest", "--tool", "libstdc++",
                                            "--srcdir=%s"%(os.path.join(libstdcppPath, "testsuite")),
                                            "-target_board=\"%sg-sim%s\"" % (cpu,cflags),
                                            "SIM=%s" % cpu_local_run])

    # Save the log files
    self.registerLogFile (os.path.join (testsuiteResults, "libstdc++.log"))
    self.registerLogFile (os.path.join (testsuiteResults, "libstdc++.sum"))

    if result == 0 or result == 1:
      # Parse the libstdc++ regression suite results
      summary = self.parse (os.path.join (testsuiteResults, "libstdc++.log"))
      self.success (summary)

    return (result == 0 or result == 1)
