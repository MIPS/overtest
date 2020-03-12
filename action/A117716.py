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

# FPU Math Library

class A117716(Action, IMGAction, KernelTest):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117716
    self.name = "FPU Math Library"

  # Execute the action.
  def run(self):
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("KL metag CVSROOT")

    self.error("About to access KL metag CVS repository. Please fix action")
    # Check out the library
    if self.version == "Latest":
      # check out using CVS
      if not self.cvsCheckout("metag/support/fplibs", cvsroot):
        self.error("Failed to check out fplibs")
    else:
      if not self.ccsCheckout("metag/support/fplibs/ccs/dir.ccs", "FPLibs", self.version, cvsroot):
        self.error("Failed to check out fplibs")

    shared_area = self.getSharedPath()
    libm_dir = os.path.join(self.getWorkPath(), "metag", "support", "fplibs", "libm_opt")

    env={}
    env['INSTALL_DIR'] = shared_area
    # Order of toolkits is important as building linux requires GCC embedded
    # and linux toolchains and using MECC also required a GCC embedded 
    # toolchain. 
    target_opt=""
    if self.testrun.getVersion("META Linux Buildroot"):
      # Build with META Linux GCC
      self.initialiseBuildSystem()
      env['METAG_LINUX_ROOT'] = self.toolkit_path
      target_opt="linux"
    elif self.testrun.getVersion("MECCToolkit"):
      # Build with MECC
      env['METAG_INST_ROOT'] = self.config.getVariable("METAG_INST_ROOT")
      env['MECC_INST_ROOT'] = self.config.getVariable("MECC_INST_ROOT")
    elif self.testrun.getVersion("MetaMtxToolkit"):
      # Build with META Embedded GCC
      env['METAG_INST_ROOT'] = self.config.getVariable("METAG_INST_ROOT")
      target_opt="metag"
    else:
      self.error("Unable to determine how to build library")

    if self.execute(command=["make", "install", "TARGET=%s" % target_opt], workdir=libm_dir, env=env) != 0:
      self.error("Unable to build double precision library")
    if self.execute(command=["make", "install", "FPSINGLE=1", "TARGET=%s" % target_opt], workdir=libm_dir, env=env) != 0:
      self.error("Unable to build single precision library")

    return self.success()
