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

