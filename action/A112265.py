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

# META Linux BusyBox

class A112265(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 112265
    self.name = "META Linux BusyBox"

  # Execute the action.
  def run(self):
    """
    Just make a Buildroot compatible patch and pass the patchfile location on
    """
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("LEEDS CVSROOT")
    env = {"CVSROOT":cvsroot};
    patchfile = os.path.join(self.getSharedPath(), "busybox-metag.patch")

    if self.version == "Latest":
      tag = "HEAD"
    else:
      tag = self.version

    exitcode = self.execute(env=env,
                            command=["cvs -q rdiff -ko -u -r busybox_1_2_1 -r %s metag-busybox/modutils/insmod.c | " % tag +\
                                     "filterdiff -# 1,4- > %s" % patchfile],
                            shell=True)

    if exitcode == 0:
      exitcode = self.execute(env=env,
                              command=["cvs -q rdiff -ko -u -r busybox_1_2_1 -r %s metag-busybox | " % tag +\
                                       "filterdiff -x '*/insmod.c' | "+\
                                       "filterdiff -x '*/.config' | "+\
                                       "filterdiff -x '*/Rules.mak' >> %s" % patchfile],
                              shell=True)
    else:
      self.error("Failed to create initial single hunk patch")
     
    return (exitcode == 0)
