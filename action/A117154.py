import os
from Action import Action
from IMGAction import IMGAction
from common.KernelTest import KernelTest

# META Linux Linpack

class A117154(Action, IMGAction, KernelTest):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117154
    self.name = "META Linux Linpack"
    self.umask = 0

  # Execute the action.
  def run(self):
    """
    Use the KernelTest framework to grab a pre-built buildroot and test framework
    Tweak the filesystem so that it has the correct startup scripts
    Use the KernelTest framework to rebuild the filesystem
    Use the KernelTest framework to build the kernel
    Use the KernelTest framework to Put the bootable package together
    Use the KernelTest framework to Run the test
    Process the results
    """

    if not self.fetchLinuxBuildSystem():
      return False

    # Adjust the filesystem
    if self.execute(workdir=self.buildroot_dir,
                    command=[os.path.join(self.testbench_dir, "prepare_test.sh"), "linpackc"]) != 0:
      self.error("Failed to adjust filesystem to boot to linpack")

    host = self.getResource ("Execution Host")
    cvsroot = host.getAttributeValue ("LEEDS CVSROOT")
    # Checkout coremark
    if not self.cvsCheckout(module="metag-linux-benchmarks/linpackc",
                            cvsroot=cvsroot):
      self.error("Failed to check out linpack source")

    env = { "PATH":"%s:%s" % (self.compiler_path, os.environ['PATH']) }
    # Build coremark
    if self.execute(workdir=os.path.join(self.getWorkPath(), "metag-linux-benchmarks", "linpackc"),
                    command=["make"],
                    env=env) != 0:
      self.error("Failed to build linpack")

    # Install coremark
    if self.installIntoFilesystem(os.path.join("metag-linux-benchmarks", "linpackc"),
                                  os.path.join("root")):
      self.error("Failed to install linpack preserving timestamps")

    if not self.rebuildFilesystem ():
      return False

    if not self.buildKernel():
      return False

    if not self.prepareBootloader():
      return False

    self.executeKernelTest()
    console_log = self.fetchOutput().splitlines()

    currentLog = []

    tests = {}
    tests["Linpack DF Rolled"] = {"pass": False, "extended": {}}
    tests["Linpack DF Un-Rolled"] = {"pass": False, "extended": {}}
    tests["Linpack SF Rolled"] = {"pass": False, "extended": {}}
    tests["Linpack SF Un-Rolled"] = {"pass": False, "extended": {}}
    linpack_df_roll = None
    linpack_df_unroll = None
    linpack_sf_roll = None
    linpack_sf_unroll = None

    clockSpeed = None
    shouldLog = False
    for line in console_log:
      if line.startswith("#### OVT START "):
        currentLog = []
        shouldLog = True
        continue
      elif line.startswith("#### OVT END "):
        # store the cpuinfo        
        if line.endswith("PROC CPUINFO ####"):
          cpuinfo = currentLog
          for line in cpuinfo:
            if line.startswith("Clocking:\t"):
              try:
                clockSpeed = float(line[10:-3])
              except ValueError:
                pass
        elif line.endswith("LINPACK DF ROLL LOG ####"):
          linpack_df_roll = currentLog
          tests["Linpack DF Rolled"] = {"pass": True}
          tests["Linpack DF Rolled"]["extended"] = self.processLinpackLog(linpack_df_roll)
        elif line.endswith("LINPACK DF UNROLL LOG ####"):
          linpack_df_unroll = currentLog
          tests["Linpack DF Un-Rolled"] = {"pass": True}
          tests["Linpack DF Un-Rolled"]["extended"] = self.processLinpackLog(linpack_df_unroll)
        elif line.endswith("LINPACK SF ROLL LOG ####"):
          linpack_sf_roll = currentLog
          tests["Linpack SF Rolled"] = {"pass": True}
          tests["Linpack SF Rolled"]["extended"] = self.processLinpackLog(linpack_sf_roll)
        elif line.endswith("LINPACK SF UNROLL LOG ####"):
          linpack_sf_unroll = currentLog
          tests["Linpack SF Un-Rolled"] = {"pass": True}
          tests["Linpack SF Un-Rolled"]["extended"] = self.processLinpackLog(linpack_sf_unroll)
        shouldLog = False

      if shouldLog == True:
        currentLog.append(line)

    self.writeLogAndRegister("cpuinfo.log", "\n".join(cpuinfo))
    if linpack_df_roll != None:
      self.writeLogAndRegister("linpack_df_roll.log", "\n".join(linpack_df_roll))
    if linpack_df_unroll != None:
      self.writeLogAndRegister("linpack_df_unroll.log", "\n".join(linpack_df_unroll))
    if linpack_sf_roll != None:
      self.writeLogAndRegister("linpack_sf_roll.log", "\n".join(linpack_sf_roll))
    if linpack_sf_unroll != None:
      self.writeLogAndRegister("linpack_sf_unroll.log", "\n".join(linpack_sf_unroll))

    passcount = 0
    for test in tests:
      extended = tests[test]['extended']
      extended['Clock (MHz)'] = clockSpeed
      try:
        extended['Mark'] = (float(extended["Kflops"]) / clockSpeed)
      except (KeyError, TypeError, ZeroDivisionError):
        extended['Mark'] = float(0)
      if tests[test]['pass']:
        passcount += 1
      self.testsuiteSubmit(test, tests[test]['pass'], extended)

    return self.success({"Pass count":passcount})

  def writeLogAndRegister(self, filename, contents):
    """
    Write a file and register it as a results log

    :param filename: The name of the new log file
    :type filename: string
    :param contents: The log contents as a list of lines
    :type contents: list of strings
    """
    filename = os.path.join(self.getWorkPath(), filename)
    logfile = open(filename, "w")
    logfile.write(contents)
    logfile.close()
    self.registerLogFile(filename)

  def processLinpackLog(self, log):
    """
    Check the log output of a linkpack run and extract the repetitions and
    Kflops results

    :param log: The log file as a list of lines
    :type log: list of string
    :return: Extended result data
    :rtype: dictionary
    """
    results = {}
    for line in log:
      if "Kflops" in line and "Reps" in line:
        fields = line.strip().split(" ")
        # Rolled Single  Precision 308246 Kflops ; 1000 Reps
        reps = 0
        kflops = 0
        try:
          reps = int(fields[-2])
          kflops = int(fields[-5])
        except ValueError:
          pass
        results["Repetitions"] = reps
        results["Kflops"] = kflops
    return results

