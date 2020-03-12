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
import sys
import traceback

class ConfigException(Exception):
  """
  Configuration errors representing reading or writing non-existent or unlinked
  options. Also represents writing a value of an incorrect type.
  """
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Config Error: "+self.value

class OvtError(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Error: "+self.value

class ClaimException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Claim Error: "+self.value

class ResourceException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Resource Error: "+self.value

class ImpossibleDependencyException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Impossible Dependency Error: "+self.value

class AllocationException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Allocation Error: "+self.value

class AllocationAbortException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Allocation Abort Error: "+self.value

class ClaimReturnedException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Claim Error: "+self.value

class ResourceAlreadyClaimedException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Resource Claiming Error: "+self.value

class BadResourceStatusException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Resource Status Error: "+self.value

class DatabaseRetryException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Database retry required: "+self.value

class TestrunAbortedException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Testrun has aborted: "+self.value

class ResultSubmissionException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Result submission error: "+self.value

class StartupException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Startup error: "+self.value

class TimeoutException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Timeout error: "+self.value

class DAToolsInitException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "DA-Tools initialisation error: "+self.value

class ResourceInitFailedException(Exception):
  def __init__(self, message, transient = False):
    self.value = message
    self.transient = transient

  def __str__(self):
    extra = ""
    if self.transient:
      extra = "[TRANSIENT] "
    return "Resource initialisation error: %s%s" % (extra, self.value)

  def isTransient (self):
    return self.transient

class TaskRunErrorException(Exception):
  def __init__(self, actionid):
    self.actionid = actionid

  def __str__(self):
    return "Error running task: A%s" % self.actionid

class TimeoutException(Exception):
  def __init__(self, time):
    self.value = str(time)

  def __str__(self):
    return "Timeout error after %s seconds" % self.value

class NoQueueException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "NoQueue: %s" % self.value

class MissingVersionException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Missing version: %s" % self.value

def formatExceptionInfo():
  """
  For custom exception handling, this function will return the current stack trace
  as a string.
  """
  error_type, error_value, trbk = sys.exc_info()
  tb_list = traceback.format_tb(trbk)
  s = "Error: %s \nDescription: %s \nTraceback:" % (error_type.__name__, error_value)
  for i in tb_list:
    s += "\n" + i
  return s

