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
from Resource import Resource
from Config import CONFIG
import os
from OvertestExceptions import ResourceException, TimeoutException

class R2(Resource):
  """
  A class to manage the Debug Adapter resources
  """
  RESOURCETYPEID=2

  def __init__(self, data):
    """
    Initialise the class
    """
    Resource.__init__(self, data)

  def initialise(self):
    """
    Run the initialisation commands
    """
    try:
      da_name = self.getAttributeValue("DA Name")
    except ResourceException:
      self.error("Debug Adapter has no DA Name attribute")

    command = [CONFIG.neo, 'run_dascript', 'da_init.py', "-D", da_name]
    try:
      result = self.execute(timeout=100,command=command)
    except TimeoutException:
      return self.transientError("Timeout when initialising DA")

    if result != 0:
      self.logHelper("Warning: Could not initialise DA")
      #self.error("Failed to initialise DA, check logs")

    return True
