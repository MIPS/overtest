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
import re
import shutil
from Config import CONFIG
from Action import Action
from IMGAction import IMGAction

# MBSIM API

class A117799(Action,IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117799
    self.name = "MBSIM API"
   
  # Execute the action.
  def run(self):
    workDir = self.getWorkPath()
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("KL metag CVSROOT")
    csimPath = self.config.getVariable("METAG_FSIM_ROOT")
    buildPlat = self.config.getVariable("MetaMtxCoreSim Build")

    env = {}
    env['METAG_FSIM_ROOT'] = csimPath
    env['CVSROOT'] = cvsroot
    self.error("About to access KL metag CVS repository. Please fix scripts")

    # we need to patch just built CSim
    self.patchWithInsimevt(csimPath, cvsroot)

    say_arch = ""
    if "64" in buildPlat :
      say_arch = "X64"

    command = [CONFIG.neo,
               "sim/test_mbsimapi",
               "FSIM=%s" % self.config.getVariable("Simulator Spec"),
               "SIMTEST=%s" % self.version,
                say_arch,
               "TESTLOG_DIR=%s" % workDir]
    
    result = self.execute(command=command, env=env)
    
    if result == 1:
      return self.failure()
    else:
      if result > 1:
        self.warn("MBSIM API return value = %d" % result)

      parseResult = self.parseLogs(os.path.join(workDir, "test.log"))
      
      genStaticTests = self.config.getVariable("Generate static tests")

      if parseResult and genStaticTests:
        triggerRun = self.config.getVariable("Run static tests")
        return self.createStaticTests(workDir, cvsroot, triggerRun)
      else:
        return parseResult

  def patchWithInsimevt(self, builtCSimPath, cvsroot):
    # if we want to use older versions of Verify Toolkit we need to patch CSim sources
    # with insimevt.h file.
    if not self.cvsCheckout("metag/verify/metac/insimevt.h", cvsroot):
      self.error("Unable to check out insimevt.h file")

    insimDir = os.path.join(self.getWorkPath(), "metag", "verify", "metac")
    insimFile =  os.path.join(insimDir, "insimevt.h")

    targetDirMetag = os.path.join(builtCSimPath, "metag-local", "include", "metag")
    targetDirMtxg  = os.path.join(builtCSimPath, "mtxg-local", "include", "metag")

    targetMetagFile = os.path.join(targetDirMetag, "insimevt.h")
    targetMtgxFile  = os.path.join(targetDirMtxg,  "insimevt.h")

    try:
      if not os.path.exists(targetDirMetag):
        os.makedirs(targetDirMetag)
      if not os.path.exists(targetDirMtxg):
        os.makedirs(targetDirMtxg)
      if not os.path.exists(targetMetagFile):
        shutil.copy(insimFile, targetMetagFile)
      if not os.path.exists(targetMtgxFile):
        shutil.copy(insimFile, targetMtgxFile)
    except OSError:
        self.error("Failed to patch. Insimevt.h paths: %s, %s, %s" % (insimFile, targetMetagFile, targetMtgxFile))

  def parseLogs(self, logfile):
    try:
      testLog = open(logfile,"r")
    except IOError:
      return self.success({"Error":"Log file is missing"})
    
    lines = testLog.readlines()
    testLog.close()

    results = {}
    results['TOTAL PASSED'] = 0
    results['TOTAL FAILED'] = 0

    for l in lines:
      if re.search('#\d+:\s', l):
        lfields = l.replace("*"," ").split()
        if lfields[5] == "Passed":
          results['TOTAL PASSED'] += 1
          self.testsuiteSubmit(lfields[3], True, {"seconds":float(lfields[6])})
        else:
          results['TOTAL FAILED'] += 1
          self.testsuiteSubmit(lfields[3], False, {"seconds":float(lfields[6])})

    self.registerLogFile(logfile)
    return self.success(results)

  def getStub(self, fullVersion):
    tmp = fullVersion.split(".")
    return "%s.%s.%s" % (tmp[0], tmp[1], tmp[2])

  def getConfig(self, linesNEOLIST = None, filename = None):
    # version of just built CSim
    MetaMtxCoreSimVersion = self.config.getVariable("Version")
    
    if linesNEOLIST == None:
      VerifyToolkitVersion  = self.config.getVariable("VerifyToolkit version")
      MetaMtxToolkitVersion = self.config.getVariable("MetaMtxToolkit version")
      VerifyToolkitRoot = "root"
    else:
      coreName = filename.replace("_meta_static.yaml","")
      simVer = self.getStub(MetaMtxCoreSimVersion).replace(".","_")
      # read configuration from Neolist file
      found = 0
      for l in linesNEOLIST:
        if (simVer == "4_0_3" or simVer == "4_0_2"):
          coreLineMatch = re.match('csim\_%s\_static\_%s:.*VERIFY=([0-9\.]+).*TOOLS=([0-9\.]+)/(\S+)' %(simVer, coreName), l)
        else:  
          coreLineMatch = re.match('csim\_static\_%s:.*VERIFY=([0-9\.]+).*TOOLS=([0-9\.]+)/(\S+)' % coreName, l)
        
        if coreLineMatch:
          VerifyToolkitVersion  = coreLineMatch.group(1)
          MetaMtxToolkitVersion = coreLineMatch.group(2)
          VerifyToolkitRoot     = coreLineMatch.group(3)
          found = 1
          break
        
      if found == 0:
        self.error("Couldn't find corresponding entry in csim.NEOLIST for %s" % coreName)
    
    buildPlat = self.config.getVariable("MetaMtxCoreSim Build")
    
    arch = ""
    if "64" in buildPlat :
      arch = "x64"
    
    MetaMtxCoreSimVersionArch = MetaMtxCoreSimVersion+arch
    
    configDict = {
      "${VERIFYTOOLKIT_VERSION}"       : VerifyToolkitVersion,
      "${VERIFYTOOLKIT_STUB}"          : self.getStub(VerifyToolkitVersion),
      "${METAMTXCORESIM_VERSION}"      : MetaMtxCoreSimVersion,
      "${METAMTXCORESIM_VERSION_ARCH}" : MetaMtxCoreSimVersionArch,
      "${METAMTXCORESIM_STUB}"         : "Scratch",
      "${METAMTXTOOLKIT_VERSION}"      : MetaMtxToolkitVersion,
      "${METAMTXTOOLKIT_STUB}"         : self.getStub(MetaMtxToolkitVersion),
      "${MANUAL_SIMULATOR_ROOT}"       : self.config.getVariable("METAG_FSIM_ROOT"),
      "${METAMTXCORESIM_BUILD}"        : buildPlat,
      "${MANUAL_TOOLKIT_ROOT}"         : VerifyToolkitRoot}

    return configDict

  def createStaticTests(self, workDir, cvsroot, runNow):
    # prepare version dictionary
    useNeolist = self.config.getVariable("Use CSim NEOLIST")

    if useNeolist:
      pathNeolist = os.path.join(CONFIG.getProgramDir(CONFIG.neo), "csim.NEOLIST")
      try:
        fileNeolist = open(pathNeolist,"r")
        dataNeolist = fileNeolist.readlines()
        fileNeolist.close()
      except IOError:
        return self.failure({"Error":"Reading csim.NEOLIST file failed"})
    
    # checkout YAML files into work directory
    if not self.cvsCheckout("metag/tools/tests/simtests/yaml", cvsroot):
      self.error("Unable to check out yaml files")
    
    yamlDirectory = os.path.join(self.getWorkPath(), "metag", "tools", "tests", "simtests", "yaml")
    
    # replace proper strings in all YAML files (create copy of each)
    testruns = []
    for file in os.listdir(yamlDirectory):
      if not file.endswith("meta_static.yaml"):
        continue
      try:
        srcFilePath = os.path.join(yamlDirectory, file)
        dstFilePath = os.path.join(workDir, "ready-%s" % file)
        srcFile = open(srcFilePath, 'r')
        dstFile = open(dstFilePath, 'w')
        testruns.append(dstFilePath)

        # get proper verify and toolkit versions
        if useNeolist:
          yamlDict = self.getConfig(dataNeolist, file)
        else:
          yamlDict = self.getConfig()

        # replace fields
        text = srcFile.read()
        for key, value in yamlDict.items():
          text = text.replace(key, value)
        dstFile.write(text)

        srcFile.close()
        dstFile.close()
      except IOError:
        return self.failure({"Error":"Couldn't replace strings in YAML files"})

    host = self.getResource("Execution Host")
    filesystem = host.getAttributeValue("Shared Filesystem")
    hostid = host.getAttributeValue("Specific Host")

    # generate and run all tests!
    for t in testruns: 
      command = [CONFIG.neo, "overtest", "-t",
                 "--new",
                 "-u", "testsim",
                 "--file", t,
                 "--type", "Execution Host",
                 "--attribute", "Specific Host",
                 "--value", hostid]
      if runNow:
        command.append("--go")

      result = self.execute(command=command)

      if result != 0:
        self.error("Creating the testruns failed")
     
    if testruns:
      return self.success()
    else:
      return self.failure({"Error":"Creating the testruns dynamically failed"})
