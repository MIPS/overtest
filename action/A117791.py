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

# DA Build

class A117791(Action,IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117791
    self.name = "DA Build"

  # Execute the action.
  def run(self):

    # Get the METAG_INST_ROOT and add it to the environment
    METAG_INST_ROOT = self.config.getVariable("METAG_INST_ROOT")
    env = {}
    env['PATH'] = METAG_INST_ROOT+"/bin:"+os.environ['PATH']
    env['METAG_INST_ROOT'] = METAG_INST_ROOT

    # Get the CVSROOT
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("LE firmware CVSROOT")

    # Checkout the Dash source
    if not self.cvsCheckout("DashNG", cvsroot=cvsroot):
      self.error("Unable to checkout source!")
   
    dash_dir = os.path.join(self.getWorkPath(), "DashNG")

    # Patch the source
    if self.execute(command=["patch", "-p0", "-itools/GCC4/linux.patch"], workdir=dash_dir, env=env) != 0:
      self.error("Unable to patch source!")
  
    da_type = self.config.getVariable("DA Type") 
    
    if da_type == "DA-Net":
      da_make = "net"
    elif da_type == "DA-Trace":
      da_make = "trace"
    else:
      da_make = 'unknown'
      
    # Build the source
    if self.execute (command=["make", "-fmakefile_" + da_make, "all"], workdir=dash_dir, env=env) == 0:
      return self.success()
    else:
      return self.failure()
