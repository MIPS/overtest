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
