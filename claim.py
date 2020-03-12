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
import OvtDB
import sys
from OvertestExceptions import *

ovtDB = OvtDB.OvtDB()

if len(sys.argv) == 3:
  userid = ovtDB.createOrFindUser(sys.argv[1])
  resourceid = ovtDB.getResourceByName(sys.argv[2])
  if userid == None:
    print "Username does not exist"
    usage()
  if resourceid == None:
    print "Resource does not exist"
    usage()

  try:
    if ovtDB.claimResource(userid, resourceid):
      sys.exit(0)
    else:
      sys.exit(1)
  except ResourceAlreadyClaimedException, e:
    print e
    sys.exit(1)

def usage():
  print "%s <username> <resource> "%sys.argv[0]
  print "This utility will claim the specified resource"
  print "A return code of 0 indicates success, 1 is an error"
  sys.exit(1)
