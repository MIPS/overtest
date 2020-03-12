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
import errno

def pid_exists(pid):
  try:
    os.kill(pid, 0)
    return True
  except OSError, err:
    return err.errno == errno.EPERM

def versionCompare(a, b):
  """
  Compare two version numbers passed as arrays of numbers.
  Returns -1 for a < b, 0 for a == b, and 1 for a > b.
  Convert a dotted version number to a suitable list using version.split(".")
  """
  for adigit, bdigit in zip(a, b):
    try:
      if int(adigit) < int(bdigit):
        return -1
      if int(adigit) > int(bdigit):
        return 1
    except ValueError:
      if str(adigit) < str(bdigit):
        return -1
      if str(bdigit) < str(adigit):
        return 1

  if len(a) > len(b):
    return 1

  if len(a) < len(b):
    return -1

  return 0
