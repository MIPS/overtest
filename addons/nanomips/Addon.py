import getopt
import sys
import os
from TestrunEditing import TestrunEditing, TestrunOptions
from copy import deepcopy
from OvertestExceptions import *
from TestConfigurations import GCCDejagnuTestConfig, GPPDejagnuTestConfig,\
			       GOLDTestConfig, GDBTestConfig

class Addon:
  def __init__(self, ovtDB):
    self.ovtDB = ovtDB
    self.te = TestrunEditing(ovtDB)

  def usage(self, exitcode, message):
    print "Error: %s" % message
    sys.exit(exitcode)

  def run(self, args):
    try:
      opts, args = getopt.getopt(args, "", ["binutils=","gcc=","gdb=","newlib=",
					    "musl=","smallclib=",
					    "gold=", "packages=", "dejagnu=",
					    "qemu=",
					    "components=","groupname=",
					    "version=","storage=","tot",
					    "runlist="])
    except getopt.GetoptError, e:
      self.usage(2, str(e))

    if len(opts) == 0:
      self.usage(2, "One or more options are required")

    source_tags={}
    version_name=None
    storage=None
    groupname=None
    tot=False
    runlist="source,cross,canadian,elf,linux-musl,img,g++,gcc,gnusim,binutils,gold,gdb".split(",")

    for (o,a) in opts:
      if o in ("--binutils"):
	source_tags['Binutils Branch'] = a
      elif o in ("--gcc"):
	source_tags['GCC Branch'] = a
      elif o in ("--gdb"):
	source_tags['GDB Branch'] = a
      elif o in ("--newlib"):
	source_tags['Newlib Branch'] = a
      elif o in ("--musl"):
	source_tags['Musl Branch'] = a
      elif o in ("--qemu"):
	source_tags['QEMU Branch'] = a
      elif o in ("--gold"):
	source_tags['GOLD Branch'] = a
      elif o in ("--smallclib"):
	source_tags['SmallClib Branch'] = a
      elif o in ("--packages"):
	source_tags['Packages Branch'] = a
      elif o in ("--dejagnu"):
	source_tags['Dejagnu Branch'] = a
      elif o in ("--components"):
	source_tags['Binutils Branch'] = a
	source_tags['GCC Branch'] = a
	source_tags['GOLD Branch'] = a.replace("nanoMIPS-","nanoMIPS-GOLD-")
	source_tags['GDB Branch'] = a.replace("nanoMIPS-","nanoMIPS-GDB-")
	source_tags['Newlib Branch'] = a
	source_tags['SmallClib Branch'] = a
	source_tags['Packages Branch'] = a
	source_tags['Dejagnu Branch'] = a
	source_tags['QEMU Branch'] = a
	source_tags['Musl Branch'] = a
      elif o in ("--groupname"):
	groupname = a
      elif o in ("--version"):
        version_name = a
      elif o in ("--storage"):
        storage = a
      elif o in ("--tot"):
        tot = True
      elif o in ("--runlist"):
	newrunlist = a.split(",")
	print newrunlist
	foundnegated = False
	foundpositive = False
	for newrun in newrunlist:
	  if newrun.startswith("-"):
	    foundnegated = True
	  else:
	    foundpositive = True
	if foundnegated and not foundpositive:
	  for newrun in newrunlist:
	    if newrun[1:] in runlist:
	      runlist.remove(newrun[1:])
	else:
	  runlist = newrunlist

    if storage == None or not storage.startswith("/"):
      print "An absolute path to store deliverables must be specified"
      sys.exit(1)

    if groupname == None:
      print "A group name for the builds must be specified"
      sys.exit(1)

    self.source_tags = source_tags
    self.version_name = version_name
    self.storage = storage
    self.groupname = groupname
    self.runlist = runlist
    self.tot = tot

    try:
      if "binutils" in self.runlist:
	tests = self.getBinutilsTestConfig()
	for test in tests:
	  self.gridExec(test)
	  print "created %d - %s" % (test.testrunid, test.description)
      if "source" in self.runlist:
	sourcerel = self.getSourceReleaseConfig()
	self.gridExec(sourcerel)
	print "created %d - %s" % (sourcerel.testrunid, sourcerel.description)
      lasttestrunid = None
      for os_part in ["elf", "linux-musl"]:
	if not os_part in self.runlist:
	  continue
	primary = self.getCrossBuildConfig("", os_part)
	if "cross" in self.runlist:
	  self.gridExec(primary)
	  lasttestrunid = primary.testrunid
	  print "created %d - %s" % (primary.testrunid, primary.description)
	else:
	  print "Not building toolchains, assuming standard package names in %s" % self.storage
	secondary = []
	if "canadian" in self.runlist:
	  secondary.extend(self.getCanadianBuildConfig("", os_part))
	for build in secondary:
	  if "cross" in self.runlist:
	    build.deptestrunid = primary.testrunid
	  if lasttestrunid != None:
	    build.deptestrunid = lasttestrunid
	  build.config['MIPS Prebuilt']['Manual Toolchain Root'] = primary.config['MIPS Build']['Install Root']
	  self.gridExec(build)
          lasttestrunid = build.testrunid
	  print "created %d - %s" % (build.testrunid, build.description)

	tests = []
	# Iterate over all the relevant testsuites gathering the
	# test definition and configuration options for each one
	# testsuites also know what concurrency suits them best
	use_gnusim = "gnusim" in self.runlist and os_part != "linux-musl"
	for testsuite in ["gcc", "g++", "gold", "gdb"]:
	  if not testsuite in self.runlist:
	    continue
	  if testsuite == "gcc":
	    testconfigs = GCCDejagnuTestConfig(use_gnusim)
	  elif testsuite == "g++":
	    testconfigs = GPPDejagnuTestConfig(use_gnusim)
	  elif testsuite == "gold":
	    testconfigs = GOLDTestConfig()
	  elif testsuite == "gdb":
	    testconfigs = GDBTestConfig()
	  testconfigs.tot = self.tot
	  if os_part == "linux-musl":
	    tests.extend(testconfigs.get_p32_linux_configs())
	  elif os_part == "elf":
	    tests.extend(testconfigs.get_p32_elf_configs())
	for test in tests:
	  if "cross" in self.runlist:
	    test.deptestrunid = primary.testrunid
	  if lasttestrunid != None:
	    test.deptestrunid = lasttestrunid
	  if not use_gnusim:
	    test.config['MIPS Prebuilt']['Manual QEMU Root'] = "/scratch/overtest/qemu"
	  test.config['MIPS Prebuilt']['Manual Toolchain Root'] = primary.config['MIPS Build']['Install Root']
	  if len(self.source_tags) > 0:
	    test.config['MIPS Tools'] = self.source_tags
	  self.gridExec(test)
	  print "created %d - %s" % (test.testrunid, test.description)

    except OvtError, e:
      print e
      sys.exit(1)

  def gridExec(self, opts):
    # Set up the overall testrun information to place it in the right
    # group and send it to the HH UGE
    opts.groupname = self.groupname
    if 'Execution Host' in opts.resourcerequirements:
      requirements = opts.resourcerequirements['Execution Host']
    else:
      requirements = {}
      opts.resourcerequirements['Execution Host'] = requirements
    requirements['Shared Filesystem'] = ["SC Cluster"]
    #opts.usegridengine = True
    opts.autoarchive = True
    # Start immediately 
    opts.go = True
    # Submit the testrun
    self.te.doTestrunEditing(opts)

  def getBinutilsTestConfig(self):
    tests = []
    t = TestrunOptions("new")
    t.concurrency = 1
    if len(self.source_tags) > 0:
      t.config['MIPS Tools'] = self.source_tags

    actions = {}
    actions['Binutils'] = "Remote"
    actions['Dejagnu'] = "Remote"

    t.tasks['MIPS Toolchain'] = actions

    actions = {}
    actions['Binutils Test'] = "Standalone"

    t.tasks['MIPS Testing'] = actions

    config = {}
    t.config['Binutils Testing'] = config

    targets = ["nanomips-elf",
               "nanomipseb-elf"]
    for target in targets:
      t = deepcopy(t)
      t.config['Binutils Testing']['Target'] = target
      t.description = "Binutils - %s" % target
      tests.append(t)
    
    return tests

  def getSourceReleaseConfig(self):
    t = TestrunOptions("new")
    t.concurrency = 6
    if len(self.source_tags) > 0:
      t.config['MIPS Tools'] = self.source_tags

    actions = {}
    actions['Binutils'] = "Remote"
    actions['GCC'] = "Remote"
    actions['GDB'] = "Remote"
    actions['Newlib'] = "Remote"
    if not self.tot:
      actions['SmallClib'] = "Remote"
    actions['GOLD'] = "Remote"
    actions['Musl'] = "Remote"
    actions['QEMU'] = "Remote"
    actions['Toolchain Source'] = "All - musl - qemu"

    t.tasks['MIPS Toolchain'] = actions

    t.description = "Source Release"

    config = {}
    t.config['MIPS Build'] = config
    t.config['MIPS Build']['Install Root'] = os.path.join(self.storage, "src")
    t.config['MIPS Build']['Release Version'] = self.version_name
    
    return t

  def getCrossBuildConfig(self, vendor, os_part):
    target_triple = "nanomips-%s" % (os_part)
    t = TestrunOptions("new")
    t.concurrency = 6
    config = {}
    config['Vendor'] = "none" 
    config['Architecture'] = "nanomips"
    t.config['MIPS Build'] = config
    if len(self.source_tags) > 0:
      t.config['MIPS Tools'] = self.source_tags

    host_triple = "x86_64-pc-linux-gnu"
    config = {}
    config['Host Triple'] = host_triple
    config['Host Version'] = "4.9.4-centos6"
    t.config['MIPS Host'] = config

    actions = {}
    actions['Binutils'] = "Remote"
    actions['GCC'] = "Remote"
    actions['GDB'] = "Remote"
    actions['GOLD'] = "Remote"
    actions['Packages'] = "Remote"
    actions['Dejagnu'] = "Remote"
    if os_part == "elf":
      actions['Newlib'] = "Remote"
      if self.tot:
	actions['Toolchain Build'] = "Bare Metal - nosmallclib"
      else:
        actions['SmallClib'] = "Remote"
        actions['QEMU'] = "Remote"
	actions['Toolchain Build'] = "Bare Metal - qemu"
    else:
      actions['Musl'] = "Remote"
      actions['QEMU'] = "Remote"
      actions['Toolchain Build'] = "Linux - musl,qemu"

    t.tasks['MIPS Toolchain'] = actions

    t.description = "%s %s" % (target_triple, host_triple)
    primary_install = os.path.join(self.storage, "%s_%s.tgz" % (target_triple, host_triple))
    t.config['MIPS Build']['Install Root'] = primary_install
    t.config['MIPS Build']['Release Version'] = self.version_name
    
    return t

  def getCanadianBuildConfig(self, vendor, os_part):
    target_triple = "nanomips-%s" % (os_part)
    t = TestrunOptions("new")
    t.concurrency = 6
    config = {}
    config['Vendor'] = "none" 
    config['Architecture'] = "nanomips"
    t.config['MIPS Build'] = config
    if len(self.source_tags) > 0:
      t.config['MIPS Tools'] = self.source_tags

    host_triple = "i686-pc-linux-gnu"
    config = {}
    config['Host Triple'] = host_triple
    config['Host Version'] = "4.9.4-centos6"
    t.config['MIPS Host'] = config

    config = {}
    config['Manual Triple'] = target_triple
    t.config['MIPS Prebuilt'] = config

    actions = {}
    actions['Binutils'] = "Remote"
    actions['GCC'] = "Remote"
    actions['GOLD'] = "Remote"
    actions['GDB'] = "Remote"
    actions['QEMU'] = "Remote"
    actions['Packages'] = "Remote"
    actions['Dejagnu'] = "Remote"
    if os_part == "elf":
      actions['Toolchain Build'] = "Bare Metal - Canadian Cross - qemu"
    else:
      actions['Toolchain Build'] = "Linux - Canadian Cross - musl,qemu"
	
    actions['Toolchain Prebuilt'] = "Custom"
    t.tasks['MIPS Toolchain'] = actions

    t.description = "%s %s" % (target_triple, host_triple)
    secondary_install = os.path.join(self.storage, "%s_%s.tgz" % (target_triple, host_triple))
    t.config['MIPS Build']['Install Root'] = secondary_install
    t.config['MIPS Build']['Release Version'] = self.version_name

    secondary_runs = [t]

    t = deepcopy(t)

    host_triple = "i686-w64-mingw32"
    t.config['MIPS Host']['Host Triple'] = host_triple
    t.config['MIPS Host']['Host Version'] = "4.9.4_v3.1.0"
    t.description = "%s %s" % (target_triple, host_triple)
    secondary_install = os.path.join(self.storage, "%s_%s.tgz" % (target_triple, host_triple))
    t.config['MIPS Build']['Install Root'] = secondary_install

    secondary_runs.append(t)

    t = deepcopy(t)

    host_triple = "x86_64-w64-mingw32"
    t.config['MIPS Host']['Host Triple'] = host_triple
    t.description = "%s %s" % (target_triple, host_triple)
    secondary_install = os.path.join(self.storage, "%s_%s.tgz" % (target_triple, host_triple))
    t.config['MIPS Build']['Install Root'] = secondary_install

    secondary_runs.append(t)
    
    return secondary_runs

  def getGridYAML(self):
    t = {}
    attrs = {}
    attrs['Shared Filesystem'] = "HH UGE"
    t['resources'] = [ { "Execution Host" : attrs } ]
    t['usegridengine'] = True
    return t

  def compareResults(self):
    t1_groupid = self.ovtDB.simple.getTestrunGroupByName(group1)
    t2_groupid = self.ovtDB.simple.getTestrunGroupByName(group2)
    categoryid = self.ovtDB.simple.getActionCategoryByName(category)
    actionid = self.ovtDB.simple.getActionByName(action)

    sql = "SELECT t1.testrunid, t2.testrunid "+\
	  "FROM ovt_testrun AS t1 INNER JOIN ovt_testrun AS t2 USING (description) "+\
	  "     INNER JOIN ovt_testrunaction AS ta1 ON (t1.testrunid = ta1.testrunid) "+\
	  "     INNER JOIN ovt_testrunaction AS ta2 ON (t2.testrunid = ta2.testrunid) "+\
	  "     INNER JOIN ovt_versionedaction AS va1 ON (va1.versionedactonid = ta1.versionedactionid) "+\
	  "     INNER JOIN ovt_versionedaction AS va2 ON (va2.versionedactonid = ta2.versionedactionid) "+\
	  "WHERE t1.testrungroupid = %s "+\
	  "AND t2.testrungroupid = %s "+\
	  "AND va1.actionid = va2.actionid "+\
	  "AND va1.actionid = %s "+\
	  "ORDER BY t1.description"

    (t1_groupid, t2_groupid, actionid)


