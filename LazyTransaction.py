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

class ImpossibleInputException(Exception):
  def __init__(self, my_str):
    self.my_str = my_str

  def __str__(self):
    return self.my_str

class CannotCreateException(Exception):
  def __init__(self, my_str):
    self.my_str = my_str

  def __str__(self):
    return "Cannot create %s"%self.my_str

class InconsistentValueException(Exception):
  def __init__(self, my_str):
    self.my_str = my_str

  def __str__(self):
    return "Value of %s is inconsistent with existing database value"%self.my_str

class Placeholder:
  """ A placeholder for an ID that has not been created yet """

  def __init__(self):
    self.id  = None
    self.ref = None

class ActionLocker:
  """ An instruction to lock an action """
  def __init__(self, id):
    self.id = id

class LazyProcessing:
  """ An instruction to do some processing when it's possible """

  def canProcess(self):
    """ True if this can be processed """
    return True

  def process(self):
    """ Perform the processing """
    assert False

  def expand(self, placeholder):
    """ Expand this instruction using newly created ID """
    pass

  def getSubProcessing(self):
    """ Return a list of subprocessing to be performed """
    return []

class LazyConfigOptionLink(LazyProcessing):
  """ An instruction to link a config option """
  def __init__(self, versionedaction_id, cfgopt_id):
    self.versionedaction_id = versionedaction_id
    self.cfgopt_id = cfgopt_id

  def __str__(self):
    return "LazyConfigOptionLink %s -> %s"%(self.versionedaction_id, self.cfgopt_id)

  def canProcess(self):
    return not isinstance(self.versionedaction_id, Placeholder) and not isinstance(self.cfgopt_id, Placeholder)

  def process(self, actionimport):
    self.id = actionimport.ovtDB.createConfigOptionLink (self.versionedaction_id, self.cfgopt_id)
    actionimport.verboseExecute("new config option link")

  def expand(self, placeholder):
    if self.versionedaction_id == placeholder:
      self.versionedaction_id = placeholder.ref.id

class LazyConfigOptionLookupLink(LazyProcessing):
  """ An instruction to link a config option lookup """
  def __init__(self, versionedaction_id, cfgoptlookup_id):
    self.versionedaction_id = versionedaction_id
    self.cfgoptlookup_id = cfgoptlookup_id

  def __str__(self):
    return "LazyConfigOptionLookupLink %s -> %s"%(self.versionedaction_id, self.cfgoptlookup_id)

  def canProcess(self):
    return not isinstance(self.versionedaction_id, Placeholder) and not isinstance(self.cfgoptlookup_id, Placeholder)

  def process(self, actionimport):
    self.id = actionimport.ovtDB.createConfigOptionLookupLink (self.versionedaction_id, self.cfgoptlookup_id)
    actionimport.verboseExecute("new config option lookup link")

  def expand(self, placeholder):
    if self.versionedaction_id == placeholder:
      self.versionedaction_id = placeholder.ref.id

class LazyAttributeValueLink(LazyProcessing):
  """ An instruction to link an attribute value """
  def __init__(self, versionedaction_id, attrval_id):
    self.versionedaction_id = versionedaction_id
    self.attrval_id = attrval_id

  def __str__(self):
    return "LazyAttributeValueLink %s -> %s"%(self.versionedaction_id, self.attrval_id)

  def canProcess(self):
    return not isinstance(self.versionedaction_id, Placeholder) and not isinstance(self.attrval_id, Placeholder)

  def process(self, actionimport):
    self.id = actionimport.ovtDB.createResourceRequirement (self.versionedaction_id, self.attrval_id)
    actionimport.verboseExecute("new attribute value link")

  def expand(self, placeholder):
    if self.versionedaction_id == placeholder:
      self.versionedaction_id = placeholder.ref.id

class LazyDependency(LazyProcessing):
  """ An instruction to create a dependency """
  def __init__(self, producer_id, consumer_id, depgroup=None, hostmatch=None, versiononly=None, defaultdep=None):
    self.producer_id = producer_id
    self.consumer_id = consumer_id
    self.hostmatch   = hostmatch
    self.versiononly = versiononly
    self.defaultdep  = defaultdep
    self.depgroup = depgroup

  def __str__(self):
    return "LazyDependency %s -> %s"%(self.producer_id, self.consumer_id)

  def canProcess(self):
    return not isinstance(self.producer_id, Placeholder) and not isinstance(self.consumer_id, Placeholder)

  def process(self, actionimport):
    data = {}
    data['hostmatch']   = self.hostmatch
    data['versiononly'] = self.versiononly
    data['defaultdep']  = self.defaultdep
    data['dependencygroupid'] = self.depgroup
      
    actionimport.ovtDB.createDependency (self.producer_id, self.consumer_id, None, data)
    actionimport.verboseExecute("new dependency")

  def expand(self, placeholder):
    if self.producer_id == placeholder:
      self.producer_id = placeholder.ref.id
    if self.consumer_id == placeholder:
      self.consumer_id = placeholder.ref.id

class LazyVersionedAction(LazyProcessing):
  """ An instruction to create a versioned action """
  def __init__(self, placeholder, name, action_id, cfgopts, producers, consumers, resources, lifecyclestate):
    self.placeholder = placeholder
    self.placeholder.ref = self
    self.name = name
    self.action_id = action_id
    self.cfgopts = cfgopts
    self.producers = producers
    self.consumers = consumers
    self.resources = resources
    self.lifecyclestate = lifecyclestate

  def __str__(self):
    return "LazyVersionedAction %s (%s)"%(self.name, self.placeholder)

  def canProcess(self):
    return self.name != None and self.action_id != None

  def process(self, actionimport):
    data = { 'name' : self.name, 'actionid' : self.action_id, 'lifecyclestateid' : self.lifecyclestate }

    self.id = actionimport.ovtDB.addVersionedAction (data)
    actionimport.verboseExecute("new versioned action %s"%self.id)

  def getSubProcessing(self):
    work = []
    work.extend (self.cfgopts)
    work.extend (self.producers)
    work.extend (self.consumers)
    work.extend (self.resources)
    return work

  def expand(self, placeholder):
    for y in [self.cfgopts, self.producers, self.consumers, self.resources]:
      for x in y:
        x.expand (placeholder)

class LazyTransaction:
  ovtDB = None

  def __init__(self, _ovtDB, verbose_execute = False):
    self.ovtDB = _ovtDB
    self.verbose_execute = verbose_execute

  def verboseExecute(self, my_str):
    if self.verbose_execute:
      print my_str

  def execute(self, work):
    """
    Perform a lazy transaction.
    If already in a transaction (autocommit off) then transaction errors are not handled.
    If not in a transaction, then transaction errors either roll back and raise an exception or automatically retry
    Assumes no advisory locks are held.
    """
    success = False
    while not success:
      try:
        old_autocommit = self.ovtDB.setAutoCommit(False)

        # Separate the locks from the work
        locks = filter(lambda x: isinstance(x, ActionLocker), work)
        work  = [ x for x in work if x not in locks ]
        # Obtain all the locks that we will need
        self.obtainAllLocks (locks)

        # Update the DB according to the work list
        current_work = work
        while len(current_work) > 0:
          at_least_one_processed = False
          skipped_work  = [] # Any work that can't be done yet
          finished_work = [] # Any work the was done successfully
          new_work      = [] # Any work that was added during this pass

          for task in current_work:
            if task.canProcess():
              self.verboseExecute("do %s"%task)
              at_least_one_processed = True

              task.process (self)
              finished_work.append (task)
              new_work.extend (task.getSubProcessing ())
            else:
              self.verboseExecute ("defer %s"%task)
              skipped_work.append (task)

          if not at_least_one_processed:
            raise ImpossibleInputException('Cannot process all tasks')

          current_work = list(skipped_work)
          current_work.extend(new_work)
          for x in current_work:
            for y in finished_work:
              # Only attempt to expand those elements that have placeholders,
              # this indicates that they are newly created.
              # The only new element that can be created is a versioned action
              # and these are the only lazy transactions that have placeholders.
              # All other elements are links between various entities and these
              # newly constructed links never form the basis for a further link
              # therefore do not need to be used as expansions. All new
              # versioned actions are always created on the first iteration
              # hence the loop only iterates twice.
              if hasattr(y, 'placeholder'):
                self.verboseExecute ("expand %s with %s"%(x,y))
                x.expand (y.placeholder)

        self.releaseAllLocks (locks)

        if old_autocommit == True:
          self.ovtDB.FORCECOMMIT()
      except DatabaseRetryException, e:
        if not old_autocommit:
          raise
      except Exception, e:
        # Cancel the transaction and re-raise
        if old_autocommit:
          self.ovtDB.FORCEROLLBACK()
        raise
      else:
        success = True
        self.ovtDB.setAutoCommit (old_autocommit)

  def obtainAllLocks(self, locks):
    self.ovtDB.LOCKACTIONS ([lock.id for lock in locks])

  def releaseAllLocks(self, locks):
    self.ovtDB.UNLOCKACTIONS ([lock.id for lock in locks])

  def error(self, error):
    """
    Print an error message
    """
    print "ERROR: %s"%error
