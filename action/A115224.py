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
import sys

# META Linux Hello World

class A115224(Action, IMGAction, KernelTest):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 115224
    self.name = "META Linux Hello World"
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
    path = os.path.join(self.testbench_dir, "prepare_test.sh")
    cmd = [path, "hello"]
    if self.execute(workdir=self.buildroot_dir, command=cmd) != 0:
      self.error("Failed to adjust filesystem to boot Hello World")

    if not self.rebuildFilesystem():
      return False

    if not self.buildKernel():
      return False

    if not self.prepareBootloader():
      return False

    self.testsuiteSubmit("Hello World", self.executeKernelTest())

    return self.success({"Pass count":1})
