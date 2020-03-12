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
from action.Action import Action
from action.IMGAction import IMGAction
from Config import CONFIG
from OvertestExceptions import ConfigException

# NeoBuild
class NeoBuild(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)

  # Execute the action.
  def run(self):
    if self.version in ["Tag", "Latest"]:
      host = self.getResource("Execution Host")
      cvsroot = host.getAttributeValue("KL metag CVSROOT")

      ccs_version = ":MAX"
      head = True
      if self.version == "Tag" and self.config.getVariable("%s Tag" % self.name) != "":
        ccs_version = self.config.getVariable("%s Tag" % self.name)
        head = False

      self.error("About to access KL metag CVS repository. Please fix action")
      if not self.ccsCheckout(self.ccsfile,
                              self.name,
                              ccs_version,
                              cvsroot):
        self.error("Unable to check out %s:%s" % (self.name, ccs_version))

      if head:
        # Now update to cvs HEAD
        env = {}
        env['CVSROOT'] = cvsroot
        result = self.execute(command=[CONFIG.cvs, "update", "-A", "metag/tools"],
                              env=env)
        if result != 0:
          self.error("Unable to update to HEAD")

      # Build
      env = {}
      env['METAG_INST_ROOT'] = self.getSharedPath()
      env['NEW_INST_ROOT'] = self.getSharedPath()

      if "x64" in self.config.getVariable("%s Build" % self.name):
        env['NEOBUILD'] = "x64"
      elif "x32" in self.config.getVariable("%s Build" % self.name):
        env['NEOBUILD'] = "x32"
      elif "x86_64" in host.getAttributeValues("Processor"):
        env['NEOBUILD'] = "x64"
      else:
        env['NEOBUILD'] = "x32"

      scripts=os.path.join(self.getWorkPath(), "metag", "tools", "scripts")
      tools_quick="./tools_quick"
      tools_quick += " clean"
      debug = False
      try:
        debug = debug or self.config.getVariable("%s Debug" % self.name)
      except ConfigException:
        pass

      if debug or self.config.getVariable("MetaMtxToolkit Debug"):
        tools_quick += " debug"
      tools_quick += " %s" % self.name
      result = self.execute(command=[tools_quick], shell=True,
                            workdir=scripts, env=env)

      if result != 0:
        self.error("Unable to build %s" % self.name)

    return True
