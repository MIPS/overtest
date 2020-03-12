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
from Config import CONFIG
from Action import Action
from IMGAction import IMGAction
from OvertestExceptions import *

# MetaMtxCoreSim

class A108998(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108998
    self.name = "MetaMtxCoreSim"

  # Execute the action.
  def run(self):
    if self.version in ("Build", "BuildINFO_ON"):
      return self.fullSrcBuild()
    elif self.version == "Scratch":
      return self.getScratchSim()
    else:
      return self.neoCvsBuild()

  # Funtion to get the arcitecture of the host.
  def getHostArch(self):
    host = self.getResource("Execution Host")
    processor = host.getAttributeValues("Processor")
    if "x86_64" in processor:
      return 64
    return 32

  def setPython(self):
    distPlatform = self.config.getVariable("MetaMtxCoreSim Build")
    if "64" in distPlatform:
      self.config.setVariable("Python Spec", "2.7.2:x64")
    else:
      self.config.setVariable("Python Spec", "2.7.2:x32")

  def fullSrcBuild(self):
    """
    Build CSim from released sources (regardless of most of the parameters
    as neither coverage nor cross compile is supported at the moment).
    """
    version = self.config.getVariable("Version")

  # Get the build architecture from config options.
    distPlatform = self.config.getVariable("MetaMtxCoreSim Build")
    if "64" in distPlatform:
      if self.getHostArch() == 64 :
        arch64 = "1"
      else:  
        self.error("Cannot do 64 bit build on 32 bit host")
    else:   #32bit Build
      arch64 = "0"

    workDir = self.getSharedPath()
    env = {}
    env['PATH'] = os.environ['PATH']
    env['BUILD_VERBOSE'] = "1"

    if self.version == "BuildINFO_ON":
      cmake_opts="-DBUILD_IMGINFO=1"
    else: 
      cmake_opts=""

    command = [CONFIG.neo,
               "sim_build",
               "X64=%s" % arch64,
               "FSIM=%s" % version,
               "INSTDIR=%s" % workDir,
               "CMAKEOPT=%s" % cmake_opts,
               "TYPE=%s" % "FULL",
               "BUILDALL=1"]

    if self.execute(command=command, env=env) != 0:
      return self.failure({"Error":"sim_build failed"})

    self.config.setVariable("METAG_FSIM_ROOT", workDir)
    self.config.setVariable("Simulator Spec", "scratch")
    return self.success()

  def getScratchSim(self):
    sim_root = self.config.getVariable ("Manual Simulator Root")
    if sim_root == "":
      self.error("Scatch Sim Root not specified")
    self.config.setVariable ("Simulator Spec", "scratch")
    self.setPython()
    self.config.setVariable("METAG_FSIM_ROOT", sim_root)
    return self.success()

  def neoCvsBuild(self):
    """
    Pick proper prebuilt CSim version from neo
    """
    sim_build = self.config.getVariable("MetaMtxCoreSim Build")
    variant = None
    if sim_build != "Any":
      variant = sim_build.split()[-1]
    sim_root = None
    try:
      sim_root = self.config.getVariable ("Manual Simulator Root")
    except ConfigException:
      pass

    if sim_root == None or sim_root == "":
      if sim_build == "Any":
        sim_spec="%s/%s" % (self.version, "root")
      else:
        sim_spec="%s:%s/%s" % (self.version, variant, "root")

      self.config.setVariable ("Simulator Spec", sim_spec)
      METAG_FSIM_ROOT = self.neoSelect ("MetaMtxCoreSim", select_spec=sim_spec)
      if METAG_FSIM_ROOT == None:
        self.error("Unable to find METAG_FSIM_ROOT for %s" % (sim_spec))
      self.registerLogFile (os.path.join (METAG_FSIM_ROOT, ".neo.txt"))
    else:
      # Paths can be absolute and hence not be in neo.
      if not sim_root.startswith(os.sep):
        if variant == None:
          sim_spec="%s/%s" % (self.version, sim_root)
        else:
          sim_spec="%s:%s/%s" % (self.version, variant, sim_root)

        self.config.setVariable ("Simulator Spec", sim_spec)
        METAG_FSIM_ROOT = self.neoSelect ("MetaMtxCoreSim", select_spec=sim_spec)
        if METAG_FSIM_ROOT == None:
          self.error("Unable to find METAG_FSIM_ROOT for %s" % (sim_spec))
        self.registerLogFile (os.path.join (METAG_FSIM_ROOT, ".neo.txt"))
      else:
        self.config.setVariable ("Simulator Spec", "scratch")
        METAG_FSIM_ROOT = sim_root

    # Store installation path
    self.config.setVariable ("METAG_FSIM_ROOT", METAG_FSIM_ROOT)
    return True
