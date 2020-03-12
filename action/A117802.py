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

# AutoConfBuildTargetNative

class A117802(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117802
    self.name = "AutoConfBuildTargetNative"

  # Execute the action.
  def run(self):
    root = self.getWorkPath ()
    bld_root = os.path.join(root, 'bld')

    if self.version == 'MANUAL':
      src_root = os.path.join(root, 'src')
      manual_source = self.config.getVariable("LLVM_SRC_DIR")
      os.symlink(manual_source, src_root)
    else:
      src_root = self.config.getVariable('LLVM_AUTO_SRC_DIR')

    # TODO: Set up cross toolchain

    env = {} 

    cmd = [os.path.join(src_root, 'llvm', 'configure']
    # My build command has this but it probably isnt required:
    # cmd.append (["--build=x86_64-unknown-linux-gnu"])
    cmd.append (["--host=metag-unknown-linux-uclibc"])
    cmd.append (["--target=metag-unknown-linux-uclibc"])

    cfg_result = self.execute (command=cmd, env=env,
                               workdir=bld_root)

    if cfg_result != 0:
      self.error ("Failed to configure LLVM")

    cmd = ['make']

    bld_result = self.execute (command=cmd, env=env,
                               workdir=bld_root)

    if bld_result != 0:
      self.error ("Failed to build LLVM")

    return True
