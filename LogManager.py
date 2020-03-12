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
from Config import CONFIG
import os

class LogManager:
  def __init__(self, logname, display=False, local=False, subdir=None):
    """
    Open a handle to the relevant log file
    """
    self.log = None

    if logname != None:
      location = CONFIG.logdir
      if local:
        location = "."
      if subdir is not None:
	location = os.path.join(location, str(subdir))
      try:
        os.makedirs(location)
      except OSError:
        pass

      self.log = open(os.path.join(location, "%s.log" % logname), "a")
    self.display = display

  def __del__(self):
    """
    Clean up the log file
    """
    if self.log != None:
      self.log.close()

  def write(self, message):
    """
    Write a message to the log and optionally to the screen
    """
    if self.log != None:
      self.log.write("%s\n"% message)
      self.log.flush()
    if self.display:
      print message
