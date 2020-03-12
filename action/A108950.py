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
from Action import Action
from IMGAction import IMGAction

class A108950 (Action, IMGAction):
  cvs_toolkit_versions            = 'mecc/release/scripts/toolkit-components.sh' # Not OS path
  file_toolkit_versions           = os.path.join ('mecc', 'release', 'scripts', 'toolkit-components.sh')
  file_mecc_build                 = os.path.join ('mecc', 'release', 'scripts', 'build.sh')

  def __init__ (self, data):
    Action.__init__ (self, data)
    self.actionid = 108950
    self.name     = "Checkout mecc toolkit"

  # Execute the action.
  def run(self):
    env = {}

    # Fetch the cosy CVSROOT from the host that is executing the test!
    host = self.getResource ("Execution Host")
    cvsroot = host.getAttributeValue ("KL cosy CVSROOT")

    self.error("About to access KL cosy CVS repository. Please fix action")

    # Store the source location
    work_dir = self.getWorkPath()
    self.config.setVariable ("MECC_SOURCE_ROOT", work_dir);

    # Get all the directories involved
    self.file_toolkit_versions           = os.path.join (work_dir, A108950.file_toolkit_versions)
    self.file_mecc_build                 = os.path.join (work_dir, A108950.file_mecc_build)

    # Output the new variables
    env['CVSROOT'] = cvsroot

    self.logHelper ("Starting MECC checkout")
    if self.testrun.debug_allow_skipping and os.path.exists (self.file_toolkit_versions):
      self.testrun.skip ("Checkout toolkit version script")
    else:
      result = self.cvsCheckout (A108950.cvs_toolkit_versions, cvsroot=cvsroot)
      if not result:
        self.error ("Couldn't checkout version script")

    result = self.execute (env=env, command=[self.file_toolkit_versions, self.version])
    if not result == 0:
      self.error ("Couldn't determine Release:<version>")

    component = self.fetchOutput()
    match = re.compile ("CCS_RELEASE=\"([^\"]*)\"").search(component)
    if not match:
      self.error ("Couldn't determine release version")

    if self.testrun.debug_allow_skipping and os.path.exists (self.file_mecc_build):
      self.testrun.skip ("Checkout toolkit version script")
    else:
      release_version = match.group(1)
      result = self.ccsCheckout ("mecc/release/src.ccs", "Release", release_version, cvsroot=cvsroot)
      if not result:
        self.error ("Couldn't checkout Release:%s" % release_version)

    self.logHelper ("MECC checkout Complete")
    return self.success()
