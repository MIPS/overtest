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
from Action import Action
from IMGAction import IMGAction
from common.KernelTest import KernelTest

# Bullet Benchmarks

class A117704(Action, IMGAction, KernelTest):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117704
    self.name = "Bullet Benchmarks"

  # Execute the action.
  def run(self):

    binary_dir = self.testrun.getSharedPath("Bullet")

    da = self.getResource("Debug Adapter")
    da_name = da.getAttributeValue("DA Name")

    if self.version == "META Bare Metal":
      testnames = []
      for file in os.listdir(binary_dir):
        if file.endswith(".ldr"):
          testnames.append(file[:-4])
      for testname in testnames:
        success = (self.neoRunDAScript("onetest.py", ["-T", "5200", "-D", da_name, "%s.py" % testname], workdir=binary_dir) == 0)
        output = self.fetchOutput()
        results = self.parseReport(output.split("\n"))
        self.testsuiteSubmit(testname, success, results)

    elif self.version == "META Linux":
      self.run_meta_linux(binary_dir, da_name)
    else:
      self.error("Unknown version")

    return self.success()

  def parseReport(self, report):
    """
    Parse the report returning the overall test timings
    """
    testlist = ["3000 fall", "1000 stack", "136 ragdolls", "1000 convex",
                "prim-trimesh", "convex-trimesh", "raytests"]
    results = {}
    for line in report:
      for test in testlist:
        if ("Results for %s:" % test) in line:
          results[test] = float(line.split()[-1])
    return results

  def run_meta_linux(self, binary_dir, da_name):
    """
    Use the KernelTest framework to grab a pre-built buildroot and test framework
    Tweak the filesystem so that it has the correct startup scripts
    Use the KernelTest framework to rebuild the filesystem
    Use the KernelTest framework to build the kernel
    Use the KernelTest framework to Put the bootable package together
    Use the KernelTest framework to Run the test
    Process the results
    """
    testnames = []
    for file in os.listdir(binary_dir):
      testnames.append(file)

    if not self.fetchLinuxBuildSystem():
      return False

    # Adjust the filesystem
    if self.execute(workdir=self.buildroot_dir,
                    command=[os.path.join(self.testbench_dir, "prepare_test.sh"), "bullet"]) != 0:
      self.error("Failed to adjust filesystem to boot to coremark")

    # Install bullet 
    if self.installIntoFilesystem(binary_dir, os.path.join("root", "bullet")):
      self.error("Failed to install bullet preserving timestamps")

    if not self.rebuildFilesystem ():
      return False
    
    config_override={}
    config_override['CONFIG_ATOMICITY_IRQSOFF'] = 'y'
    config_override['CONFIG_ATOMICITY_LNKGET'] = 'n'
    if not self.buildKernel(config_override):
      return False

    fpgatimer = None
    target_board = self.getResource("Target Board")
    board_type = target_board.getAttributeValue("Board Type")
    if board_type == "FPGA":
      fpgatimer = 100

    if not self.prepareBootloader(fpgatimer=fpgatimer):
      return False

    kernelrun = self.executeKernelTest()
    console_log = self.fetchOutput().splitlines()
    currentlog = None
    logs = {}
    logcount = 0
    extendedresults = {}
    for line in console_log:
      if line == "#### OVT START PROC CPUINFO ####":
        currentlog = "cpuinfo"
        logs['cpuinfo'] = []
        logcount += 1
        continue
      elif line == "#### OVT END PROC CPUINFO ####":
        currentlog = None
      else:
        for testname in testnames:
          if line == "#### OVT START BULLET %s LOG ####" % testname:
            currentlog = testname
            logs[testname] = []
            logcount += 1
            continue
          elif line == "#### OVT END BULLET %s LOG ####" % testname:
            currentlog = None

      if currentlog == 'cpuinfo':
        if line.startswith("Clocking:\t"):
          try:
            extendedresults['Clock'] = float(line[10:-3])
          except ValueError, e:
            None
        logs['cpuinfo'].append(line)
      elif currentlog != None:
        logs[currentlog].append(line)

    passcount = 0
    if not kernelrun:
      self.testsuiteSubmit("Bullet", False, extendedresults={"Error":"Kernel crash"})
    else:
      passcount = 0
      if 'cpuinfo' in logs:
        self.writeLogAndRegister("cpuinfo.log", "\n".join(logs['cpuinfo']))

      for testname in testnames:
        results = {"Error":"Crashed during or before run"}
        passed = False
        if testname in logs:
          self.writeLogAndRegister("%s.log" % testname, "\n".join(logs[testname]))
          results = self.parseReport(logs[testname])
          passed = (len(results) == 7)

        if passed:
          passcount += 1
        self.testsuiteSubmit(testname, passed, extendedresults = results)

    extendedresults['Pass count'] = passcount
    return self.success(extendedresults)

  def writeLogAndRegister(self, filename, contents):
    """
    Write a file called filename using the string contents and register it as a log
    """
    filename = os.path.join(self.getWorkPath(), filename)
    logfile = open(filename, "w")
    logfile.write(contents)
    logfile.close()
    self.registerLogFile(filename)


