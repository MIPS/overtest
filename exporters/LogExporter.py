import sys
import os
import getopt
import urllib
import urllib2
from OvertestExceptions import *

class LogExporter:
  ovtDB = None

  def __init__(self, _ovtDB):
    self.ovtDB = _ovtDB
    self.debug_enabled = False

  def usage(self, exitcode, error = None):
    """
    Display the usage
    """
    if error != None:
      self.error(error)
      print ""
    print "Usage:"
    print "  --testrun=<id>"
    print "  --action=<name>"
    print "  --log=<filename>"
    print "  --output=<filename>"
    sys.exit (exitcode)

  def exportData(self, args):
    try:
      opts, args = getopt.getopt (args, "", ["testrun=", "category=", "action=", "log=", "output="])
    except getopt.GetoptError, e:
      self.usage (2, str(e))

    testrun_id  = None
    category_name = None
    action_name = None
    log_name    = None
    output_name = None

    for (o, a) in opts:
      if o == "--testrun":
        testrun_id = a
      elif o == "--category":
        category_name = a
      elif o == "--action":
        action_name = a
      elif o == "--log":
        log_name = a
      elif o == "--output":
        output_name = a

    if output_name == None:
      output_name = log_name

    if testrun_id == None:
      self.usage (1, "--testrun required")
    elif category_name == None:
      self.usage (1, "--category required")
    elif action_name == None:
      self.usage (1, "--action required")
    elif log_name == None:
      self.usage (1, "--log required")

    category_id  = self.ovtDB.simple.getActionCategoryByName (category_name)
    if category_id == None:
      self.error ("Unknown category")
      sys.exit (1)

    action_id    = self.ovtDB.simple.getActionByName (category_id, action_name)
    if action_id == None:
      self.error ("Unknown action")
      sys.exit (1)

    testrun_details = self.ovtDB.getTestrunDetails (testrun_id)
    if testrun_details == {}:
      self.error ("Unknown testrun")
      sys.exit (1)

    testrun_def  = testrun_details['definition'] 
    if category_name not in testrun_def:
      self.error ("Category not used in testrun")
      sys.exit (1)
    if action_name not in testrun_def[category_name]:
      self.error ("Action not used in testrun")
      sys.exit (1)

    version_name = testrun_def[category_name][action_name]

    versionedaction_id = self.ovtDB.simple.getVersionedActionByName (action_id, version_name)
    if versionedaction_id == None: 
      self.error ("Internal: Unknown version")
      sys.exit (1)

    uri = "http://overtest.le.imgtec.org/viewlog.php"

    query = []
    query.append (('testrunid', testrun_id))
    query.append (('versionedactionid', versionedaction_id))
    query.append (('log', log_name))
    query.append (('actionlog', 1))
    query.append (('download', '1'))
    query = urllib.urlencode (query)

    try:
      source = urllib2.urlopen (uri + "?" + query)
    except urllib2.HTTPError, e:
      if e.code == 404:
        self.error ("Unknown log file or not available yet")
        sys.exit(1)
      else:
        # For now rethrow
        raise e
    dest   = open (output_name, "wb")
    buf = source.read ()
    while (buf != ""):
      dest.write (buf)
      buf = source.read ()
    dest.close();

  def debug(self, debug):
    """
    Print an debug message
    """
    if self.debug_enabled:
      print "DEBUG: %s"%debug

  def error(self, error):
    """
    Print an error message
    """
    print "ERROR: %s"%error

