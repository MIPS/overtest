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
import getopt
import getpass
import os
import signal
import time
import types
import Dependencies
import subprocess
from Config import CONFIG
from DependencyCheck import DependencyCheck
from HostAllocator import HostAllocator
from LogManager import LogManager
from OvertestExceptions import *


class GridSubmitter:
  """
  Analyse a testrun to verify the dependencies
  This will also pull in any dependencies that can automatically be solved
  """
  def __init__(self, ovtDB, log = True):
    self.ovtDB = ovtDB
    self.dependencies = Dependencies.Dependencies(ovtDB)
    self.log = None
    if log:
      self.log = LogManager("grid_submitter", True)

  def termhandler(self, signum, frame):
    """
    Handle SIGTERM gracefully
    """
    self.quit = True

  def usage(self, exitcode, error = None):
    """
    Display the usage
    """
    if error != None:
      self.error(error)
      print ""
    print "Testrun Editing Usage:"
    print "-h --help"
    print "         Show this help"
    print "-u <user> --user=<user>"
    print "         The user to submit jobs for"
    sys.exit(exitcode)

  def run(self, args):
    """
    Find all testruns ready for checking and do the analysis
    """
    user = None
    userid = None
    self.quit = False
    signal.signal(signal.SIGTERM, self.termhandler)

    try:
      opts, args = getopt.getopt(args, "hu:", ["help", "user="])
    except getopt.GetoptError, e:
      raise StartupException, "Error parsing options: %s" % str(e)

    for (o,a) in opts:
      if o in ("-h", "--help"):
        self.usage(0)
      elif o in ("-u", "--user"):
        user = a

    if user == None:
      try:
        user = getpass.getuser()
      except Exception:
        None

    if user != None:
      userid = self.ovtDB.getUserByName(user)
      if userid == None:
        self.error("User '%s' does not exist" % (user))
        sys.exit(2)
    else:
      self.error("User not specified")
      sys.exit(2)

    depcheck = DependencyCheck (self.ovtDB, log=False)

    try:
      while not self.quit:
        testrunids = self.ovtDB.getTestrunsToCheck(userid)
  
        for testrunid in testrunids:
          if not depcheck.checkTestrun (testrunid, self.notify):
            self.ovtDB.setTestrunRunstatus(testrunid, "CHECKFAILED")
            self.error("Testrun failed dependency checking")
            continue


          self.ovtDB.setTestrunRunstatus(testrunid, "CHECKEDGRID")

	testrunids = self.ovtDB.getTestrunsToAllocate(userid=userid)
        for testrunid in testrunids:
          trinfo = self.ovtDB.simple.getTestrunById(testrunid)
          allocator = HostAllocator(self.ovtDB, self.log)
          allocator.allocateOneTestrun(testrunid)

          self.submitJob(testrunid, trinfo['concurrency'])

        testrunids = self.ovtDB.getGridTestrunsToArchiveOrDelete(userid)
        for (testrunid, status) in testrunids:
          if status == "READYTOARCHIVE":
            self.ovtDB.setTestrunRunstatus(testrunid, "GRIDARCHIVE")
          if status == "READYTODELETE":
	    self.ovtDB.setTestrunRunstatus(testrunid, "GRIDDELETE")

	  cmd = [CONFIG.python,
			  os.path.join(sys.path[0], "overtest.py"),
			  "-g",
			  "-i", str(testrunid)]
	  print "Testrun [%d] now archiving"
	  if subprocess.call(cmd) == 0:
	    print "Testrun [%d] archive complete"
	  else:
	    print "Testrun [%d] archive FAILED"
	  # Just archive one at a time to allow new job submission to take
	  # precedence
	  break

        # Sleep when there were no testruns to archive
	if len(testrunids) == 0:
          time.sleep(5)
    except KeyboardInterrupt, e:
      None

  def submitJob(self, testrunid, concurrency):
    from imgedaflow import gridinterface
    cmd = " ".join([CONFIG.python,
                    os.path.join(sys.path[0], "overtest.py"),
                    "-g",
                    "-j", str(int(concurrency)*2),
                    "-i", str(testrunid)])
    postcmd = os.path.join(sys.path[0], "addons", "hhuge", "cleanjob.sh")
    options = {'action'      : 'submit',
               '--cmd'       : cmd,
               '--post'      : postcmd,
               '--batch'     : True,
	       '--queue'     : "build",
	       '--mem'       : "4G",
	       '--maxmem'    : "8G",
               '--resources' : 'hdd=ssd,os=rhel6',
               '--jobname'         : "ot_%d" % testrunid}
    if concurrency > 1:
      options['--cpucores'] = str(concurrency)
      options['--uses_shared_memory'] = True
    keyactionids = self.ovtDB.getKeyActions(testrunid)
    if len(keyactionids) != 0:
      gridswitches = ",".join("%s=y"%actionid for actionid in keyactionids)
      options['--switches'] = gridswitches
    ga = gridinterface.GridAccess(**options)
    return_code, job_id = ga.run()
    self.ovtDB.registerGridJob(testrunid, job_id)
    print "Testrun [%d] started as job %s" % (testrunid, job_id)



  def notify(self, message):
    """
    Log a message
    """
    self.log.write("TR%u: %s"%(self.testrunid, message))
