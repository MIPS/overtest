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

# META Linux CoreMark

class A115316(Action, IMGAction, KernelTest):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 115316
    self.name = "META Linux CoreMark"
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
                    command=[os.path.join(self.testbench_dir, "prepare_test.sh"), "coremark"]) != 0:
      self.error("Failed to adjust filesystem to boot to coremark")

    host = self.getResource ("Execution Host")
    cvsroot = host.getAttributeValue ("KL metag CVSROOT")
    # Checkout coremark
    if not self.cvsCheckout(module="metag/support/examples/coremark/coremark_v1.0/coremark_v1.0.tgz",
                            cvsroot=cvsroot):
      self.error("Failed to check out coremark source")

    if self.execute(command=["tar", "-xzf",
                             os.path.join("metag","support","examples","coremark","coremark_v1.0","coremark_v1.0.tgz")]) != 0:
      self.error("Failed to un-tar coremark source")
    
    gcc = os.path.join(self.compiler_path, "metag-linux-gcc")
    # Build coremark
    if self.execute(workdir=os.path.join(self.getWorkPath(), "coremark_v1.0"),
                    command=["make", "load",
                             "CC=%s"%gcc,
                             "LD=%s"%gcc,
                             "PORT_DIR=linux",
                             "PORT_CFLAGS=%s"%self.config.getVariable("CoreMark flags")]) != 0:
      self.error("Failed to build coremark")

    # Install coremark
    if self.installIntoFilesystem("coremark_v1.0", os.path.join("root", "coremark")):
      self.error("Failed to install coremark preserving timestamps")

    if not self.rebuildFilesystem (extraconfig=["BR2_PACKAGE_MAKE=y"]):
      return False

    if not self.buildKernel():
      return False

    if not self.prepareBootloader():
      return False

    kernelrun = self.executeKernelTest()
    console_log = self.fetchOutput().splitlines()
    runlog = []
    cpuinfo = []
    emitcoremark = None 
    emitcpuinfo = None
    logcount = 0
    extendedresults = {}
    for line in console_log:
      if line == "#### OVT START PROC CPUINFO ####":
        if emitcpuinfo == None:
          emitcpuinfo = True
          logcount+=1
        continue
      elif line == "#### OVT START COREMARK LOG ####":
        if emitcoremark == None:
          emitcoremark = True
          logcount+=1
        continue
      elif line == "#### OVT END PROC CPUINFO ####":
        emitcpuinfo = False
      elif line == "#### OVT END COREMARK LOG ####":
        emitcoremark = False

      if emitcpuinfo != None and emitcpuinfo:
        if line.startswith("Clocking:\t"):
          try:
            extendedresults['Clock'] = float(line[10:-3])
          except ValueError, e:
            None
        cpuinfo.append(line)

      if emitcoremark != None and emitcoremark:
        if line.startswith("Iterations/Sec   : "):
          try:
            extendedresults['Iteractions/Sec'] = float(line[19:])
          except ValueError, e:
            None
        if line.startswith("Total time (secs): "):
          try:
            extendedresults['Total time (secs)'] = float(line[19:])
          except ValueError, e:
            None
        runlog.append(line)

    passcount = 0
    if not kernelrun or logcount != 2:
      self.testsuiteSubmit("CoreMark", False)
    else:
      passcount = 1
      self.writeLogAndRegister("run1.log", "\n".join(runlog))
      self.writeLogAndRegister("cpuinfo.log", "\n".join(cpuinfo))
      try:
        extendedresults['Mark'] = extendedresults['Iteractions/Sec'] / extendedresults['Clock']
      except (KeyError, TypeError, ZeroDivisionError):
        extendedresults['Mark'] = float(0)

      self.testsuiteSubmit("CoreMark", True, extendedresults)

    return self.success({"Pass count":passcount})

  def writeLogAndRegister(self, filename, contents):
    """
    Write a file called filename using the string contents and register it as a log
    """
    filename = os.path.join(self.getWorkPath(), filename)
    logfile = open(filename, "w")
    logfile.write(contents)
    logfile.close()
    self.registerLogFile(filename)


