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

# META Linux csdebug

class A115227(Action, IMGAction, KernelTest):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 115227
    self.name = "META Linux csdebug"
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

    if not self.fetchLinuxBuildSystem ():
      return False

    # Adjust the filesystem
    if self.execute (workdir=self.buildroot_dir,
                     command=[os.path.join(self.testbench_dir, "prepare_test.sh"), "csdebug", "nfs", self.nfs_server]) != 0:
      self.error("Failed to adjust filesystem to boot to LTP")

    # Check out and build csdebug
    host = self.getResource ("Execution Host")
    cvsroot = host.getAttributeValue ("LE software CVSROOT")

    version = self.version
    if version == "Latest":
      version = "HEAD"

    if not self.cvsCheckout ("applications/Linux/APP_DEBUG", cvsroot, version):
      self.error ("Failed to check out csdebug")

    # Prepare some generated headers required to build csdebug
    if not self.buildKernel (prepare=True):
      return False

    env = {}
    env['CROSS_COMPILE'] = os.path.join(self.compiler_path, "metag-linux-")
    env['LINUX_SRC'] = self.kernel_dir

    csdebug_build = os.path.join (self.getWorkPath(), "applications", "Linux", "APP_DEBUG")
    if self.execute (env=env,
                     shell=True,
                     workdir=csdebug_build,
                     command=[os.path.join (".", "makemeta2.6.sh")]) != 0:
      self.error ("Failed to build csdebug")

    # Install csdebug
    binary_path = os.path.join(csdebug_build, "meta", "2.6", "csdebug")
    if self.installIntoFilesystem(binary_path, "root"):
      self.error ("Failed to install csdebug")

    if not self.rebuildFilesystem ():
      return False

    if not self.buildKernel ():
      return False

    if not self.prepareBootloader ():
      return False

    result = self.executeKernelTest ()
    self.testsuiteSubmit ("csdebug basic", result)
    
    if result:
      result = 1
    else:
      result = 0
    return self.success({"Pass count":result})
