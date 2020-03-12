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
import time
import random
import signal
from OvertestExceptions import *
from LogManager import LogManager
from DependencyCheck import DependencyCheck

class HostAllocator:
  def __init__(self, ovtDB, log=None):
    """
    Finds testruns that are ready to be processed
    Verifies the internal consistency of the testrun
    Determines which overtest host to allocate the test to
    Locks the testrun so no further editing can happen
    """
    self.ovtDB = ovtDB
    if log == None:
      self.log = LogManager("host_allocator", True)
    else:
      self.log = log
    self.ovtDB.registerLog(self.log)
    self.depCheck = DependencyCheck(ovtDB, log=False)

  def termhandler(self, signum, frame):
    """
    Handle SIGTERM gracefully
    """
    self.quit = True

  def run(self):
    """
    Continuously perform the task
    """
    signal.signal(signal.SIGTERM, self.termhandler)
    self.quit = False
    try:
      while not self.quit:
        # Wait a bit!
        time.sleep(5)
  
        # This will find any testruns that are ready to allocate and have no
        # inter testrun dependencies that are not met
        testruns = self.ovtDB.getTestrunsToAllocate()
        
        # Fetch all the host data
        hosts = self.ovtDB.getLiveHostData()
  
        # Search for a testrun to allocate
        # This list is priority and date ordered
        for testrunid in testruns:
          try:
            # Re-check the testrun in case it has become stale and invalid. This can
            # happen as the schema is not locked until a testrun has had a host
            # allocated.
            # WORK NEEDED: This should be in a transaction with host allocation as there
            #              is still a small window of opportunity
            if not self.depCheck.checkTestrun(testrunid, notify=self.log.write):
              raise AllocationException("Testrun failed to pass checks")

            allocatethesehosts = self.findHosts(testrunid, testruns, hosts)
            # allocate all the hosts in the group to this testrun
            success = False
            while not success:
              self.ovtDB.setAutoCommit(False)
              try:
                try:
                  self.ovtDB.clearHosts(testrunid)
        
                  for hostid in allocatethesehosts:
                    self.ovtDB.allocateHost(testrunid, hostid)
                    self.log.write("Host selected: tr: %u host: %u" % (testrunid, hostid))
        
                  self.ovtDB.FORCECOMMIT()
                  success = True
                  self.ovtDB.setAutoCommit(True)
                  self.ovtDB.setTestrunRunstatus(testrunid, "HOSTALLOCATED")
                except KeyboardInterrupt, e:
                  success = True
                  self.quit = True
                  self.ovtDB.FORCEROLLBACK()
                  self.ovtDB.setAutoCommit(True)
              except DatabaseRetryException, e:
                self.log.write("Connection error, hosts deselected: tr: %u" % testrunid)
            if self.quit:
              break
          
          except AllocationException, e:
            self.ovtDB.setTestrunRunstatus(testrunid, "ALLOCATIONFAILED")
            self.log.write(e)
  
  
        # Now process all testruns that will never run because an interdependent testrun
        # action failed!
        # Mark the testrun as a complete failure!
        #testruns = getInterTestrunFailures()
    except KeyboardInterrupt, e:
      None

  def allocateOneTestrun(self, testrunid):
    try:
      allocatethesehosts = self.findHosts(testrunid)
      # allocate all the hosts in the group to this testrun
      success = False
      while not success:
        self.ovtDB.setAutoCommit(False)
        try:
          try:
            self.ovtDB.clearHosts(testrunid)
  
            for hostid in allocatethesehosts:
	      if not self.ovtDB.allocateHost(testrunid, hostid):
	        self.log.write("failed to allocate host")
              self.log.write("Host selected: tr: %u host: %u" % (testrunid, hostid))
  
            self.ovtDB.FORCECOMMIT()
            success = True
            self.ovtDB.setAutoCommit(True)
            if not self.ovtDB.setTestrunRunstatus(testrunid, "HOSTALLOCATED"):
	      self.log.write("failed to move to HOSTALLOCATED")
          except KeyboardInterrupt, e:
            success = True
            self.quit = True
            self.ovtDB.FORCEROLLBACK()
            self.ovtDB.setAutoCommit(True)
        except DatabaseRetryException, e:
          self.log.write("Connection error, hosts deselected: tr: %u" % testrunid)
    
    except AllocationException, e:
      self.ovtDB.setTestrunRunstatus(testrunid, "ALLOCATIONFAILED")
      self.log.write(e)

  def findHosts(self, testrunid, testruns=None, hosts=None):
    """
    Finds suitable hosts for testrunid using testrun info in testruns and host info in hosts
    If testruns is None then it is assumed hosts should be found for the given testrunid
    regardless of its state and the testruns and hosts must be fetched
    """
    if testruns == None:
      # Get the testrun in question
      testruns = self.ovtDB.getTestrunsToAllocate(testrunid)
    
    if hosts == None:
      # Fetch all the host data
      hosts = self.ovtDB.getLiveHostData()

    # Search for a host to run the test on (this has no ordering)
    suitablehosts = []
    for hostid in hosts:
      # WORK NEEDED: Inter testrun dependencies currently need to force same host across all testruns
      if set(testruns[testrunid]['attributes']).issubset(set(hosts[hostid]['attributes'])):
        # This host is suitable to execute this testrun
        suitablehosts.append(hostid)
  
    if len(suitablehosts) == 0:
      # WORK NEEDED: log this
      # Prepare a list of requirements for the log
      atts = str(set(testruns[testrunid]['attributes']))
      raise AllocationException("ERROR: Testrun: %u, cannot be run, no host matches the requirements:\n%s"%(testrunid, atts))
    else:
      # Now group the suitablehosts into ones that share filesystems
      filesystems = self.ovtDB.getHostFileSystems()
  
      filesystemgroups = {}
      filesystemcounts = []
      # Add the hosts into the relevant groups and add up the free space per filesystem group
      maxspace = -99999999
      chosengroup = None
      for filesystem in filesystems:
        filesystemgroups[filesystem] = []
        freespace = 0;
        for hostid in suitablehosts:
          if filesystem in hosts[hostid]['attributes']:
            freespace += (hosts[hostid]['data']['concurrency']-hosts[hostid]['activecount'])
            filesystemgroups[filesystem].append(hostid)
        if len(filesystemgroups[filesystem]) > 0 and freespace > maxspace:
          maxspace = freespace
          chosengroup = filesystem
  
      if chosengroup == None:
        raise AllocationException("ERROR: Testrun: "+str(testrunid)+", cannot be run, no host groups exist!")
  
      # Randomize when all groups are full
      if maxspace == 0:
        remove = []
        for filesystem in filesystemgroups:
          if len(filesystemgroups[filesystem]) == 0:
            remove.append(filesystem)
        for filesystem in remove:
          del filesystemgroups[filesystem]
        chosengroup = random.choice(filesystemgroups.keys())
  
      return filesystemgroups[chosengroup]
