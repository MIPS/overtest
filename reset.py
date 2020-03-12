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
#!/usr/bin/python
import VersionCheck

from OvtDB import OvtDB
import getopt
import signal
from utils.TerminalUtilities import *
from OvertestExceptions import *
from LogManager import LogManager
import resource
resource.setrlimit(resource.RLIMIT_CORE, (0,0))
(slimit, hlimit) = resource.getrlimit(resource.RLIMIT_STACK)
resource.setrlimit(resource.RLIMIT_STACK, (10485760,hlimit))

try:
  log = LogManager(None, True)
  ovtDB = OvtDB(log)
except Exception, e:
  print e
  print "Failed to connect to database"
  sys.exit(1)

if len(sys.argv) < 2:
  usage()
  sys.exit(2)
try:
  opts, args = getopt.getopt(sys.argv[1:], "i:", ["testrunid="])
except getopt.GetoptError, e:
  print e
  usage()
  sys.exit(2)

testrunid = None
(o,a) = opts[0]
if o in ("-i"):
  ovtDB.resetTestrun(int(a))

