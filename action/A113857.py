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
from OvertestExceptions import ConfigException

# MECCToolkit

class A113857(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 113857
    self.name = "MECCToolkit"

  # Execute the action.
  def run(self):
    # MECC does not support patching but does allow alternate roots to be provided
    # both within or outside of neo
    toolkit_root = ""
    try:
      toolkit_root = self.config.getVariable ("Manual MECC Toolkit Root")
    except ConfigException:
      # Manual toolkit root not supported
      pass
    MECC_INST_ROOT = None

    if toolkit_root == "":
      toolkit_root = "root"

    # Paths can be absolute and hence not be in neo. 
    if not toolkit_root.startswith(os.sep):
      self.config.setVariable ("MECC Toolkit Root", toolkit_root)
      MECC_INST_ROOT = self.neoSelect ("MECCToolkit", self.version, root=toolkit_root)
      if MECC_INST_ROOT == None:
        self.error("MECC Toolkit %s/%s not found"% (self.version,toolkit_root))
      self.registerLogFile (os.path.join (MECC_INST_ROOT, ".neo.txt")) 
    else:
      self.config.setVariable ("MECC Toolkit Root", "scratch")
      MECC_INST_ROOT = toolkit_root

    self.config.setVariable ("MECC_INST_ROOT", MECC_INST_ROOT)
    return True
