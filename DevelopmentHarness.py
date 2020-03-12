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
from OvertestExceptions import *
from utils.TerminalUtilities import *
import sys
import types
import os
from Config import CONFIG

class DevTestrun:
  def __init__(self, globals, testrunid):
    self.globals = globals
    self.testrunid = testrunid
    self.debug_allow_skipping = False
    self.log_helper_message = "TESTRUN STATUS"

  def getTestrunid(self):
    return self.testrunid

  def getResource(self, versionedactionid, name):
    if name in self.globals['resources']:
      return self.globals['resources'][name]
    else:
      raise ConfigException(name +" resource not found")

  def getTestsuite(self, actionid):
    if actionid in self.globals['testsuites']:
      return self.globals['testsuites'][actionid]
    else:
      return None

  def getConfig(self, versionedactionid):
    return DevConfig(self.globals, versionedactionid)

  def registerPID(self, versionedactionid, pid):
    pass

  def getHostPID(self):
    return 0

  def submit(self, actionnameorid, result, extendedresults = None):
    if extendedresults == None:
      extendedresults = {}
    print "Action: "+ bold(green(str(actionnameorid)))+ " reports: " + bold(green(str(result)))
    if len(extendedresults) != 0:
      print "With extended results:"
      for name in extendedresults:
        print bold(yellow(name)) +" => "+bold(green(str(extendedresults[name])))
    else:
      print "With no extended results"

  def testsuiteSubmit(self, testsuiteid, actionnameorid, result, extendedresults = None, version = "1.0"):
    if extendedresults == None:
      extendedresults = {}
    print "Assuming testsuite: "+ bold(green(str(testsuiteid)))+" is executing"
    print "Testsuite Action: "+ bold(green("%s:%s"%(actionnameorid, version)))+ " reports: " + bold(green(str(result)))
    if len(extendedresults) != 0:
      print "With extended results:"
      for name in extendedresults:
        print bold(yellow(name)) +" => "+bold(green(str(extendedresults[name])))
    else:
      print "With no extended results"

  def isAborted(self):
    return False

  def logHelper(self, status):
    print ("%s: "%(self.log_helper_message))+bold(status)

  def testFailed(self, name):
    print bold(red("ERROR: '" + name + "' FAILED"))
    sys.exit(1)

  def getVersion(self, versionedactionidoractionname):
    if not versionedactionidoractionname in self.globals['versions']:
      return None
    return self.globals['versions'][versionedactionidoractionname][0]

  def isDefaultDependency(self, consumeraction, produceraction):
    if consumeraction in self.globals['defaultdeps']:
      return produceraction in self.globals['defaultdeps'][consumeraction]
    return False

  def getSharedPath(self, versionedactionidoractionname):
    if type(versionedactionidoractionname) in types.StringTypes:
      if not versionedactionidoractionname in self.globals['versions']:
        return None
      versionedactionid = self.globals['versions'][versionedactionidoractionname][1]
    else:
      versionedactionid = versionedactionidoractionname

    return os.path.join(CONFIG.shareddir,str(self.testrunid),
                        str(versionedactionid), "shared") 

  def getUser(self):
    return self.globals['user']

class DevConfig:
  def __init__(self, globals, versionedactionid):
    self.globals = globals
    self.versionedactionid = versionedactionid

  # Config settings are hidden in one element arrays to enable them to
  # be effectively shared (and updated) between versionedactionids
  def getVariable(self, name):
    if self.versionedactionid in self.globals['config'] \
       and name in self.globals['config'][self.versionedactionid]:
      return self.globals['config'][self.versionedactionid][name][0]
    else:
      raise ConfigException(name +" variable not found")

  def setVariable(self, name, value):
    if self.versionedactionid in self.globals['config'] \
       and name in self.globals['config'][self.versionedactionid]:
      self.globals['config'][self.versionedactionid][name][0] = value
    else:
      raise ConfigException(name +" variable not found")

