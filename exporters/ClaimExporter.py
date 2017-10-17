import sys
import os
import getopt
import getpass
from utils.Utilities import versionCompare
from OvertestExceptions import *
try:
  import yaml
except ImportError:
  supports_yaml = False
else:
  supports_yaml = True

class ClaimExporter:
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
    print "-c <claimid>  --claim-id=<claimid> Specify the claim to export"
    print "-r <reason>   --reason=<reason>    Specify the claim to export using the reason"
    print "-f <file>     --file=<file>        Write the output to the file instead of"
    print "                                   stdout"
    print "-u <username> --user=<username>    Specify the user to impersonate. This should"
    print "                                   be auto-detected from your login shell"
    print "-h            --help               This help"
    sys.exit (exitcode)

  def exportData(self, args):
    try:
      opts, args = getopt.getopt (args, "c:f:r:u:h", ["claim-id=", "file=", "reason=", "user=", "help"])
    except getopt.GetoptError, e:
      self.usage (2, str(e))

    userclaimid = None
    reason = None
    user = None
    yaml_file = sys.stdout

    try:
      user = getpass.getuser()
    except Exception:
      pass

    if not supports_yaml:
      self.error ("This requires YAML support but this was not available")
      sys.exit (4)

    for (o, a) in opts:
      if o in ("-c", "--claim-id"):
        userclaimid = a
      elif o in ("-f", "--file"):
        try:
          yaml_file = open(a, "w")
        except IOError:
          self.error("Unable to open %s for writing" % a)
          sys.exit(1)
      elif o in ("-h", "--help"):
        self.usage (1)
      elif o in ("-r", "--reason"):
        reason = a
      elif o in ("-u", "--user"):
        user = a

    if user != None:
      userid = self.ovtDB.getUserByName(user)
      if userid == None:
        self.error("User '%s' does not exist" % (user))
        sys.exit(2)
    else:
      self.error("User not specified")
      sys.exit(2)

    # Must have something to dump
    if (userclaimid == None and reason == None) or \
       (userclaimid != None and reason != None):
      self.usage(2, "Either a claim number or reason must be specified")

    claim = self.ovtDB.getUserClaim(userclaimid, userid, reason)

    if claim == None:
      if userclaimid != None:
        self.error("Claim [%d] does not exist" % userclaimid)
      else:
        self.error("You have no claims with the reason '%s'"
                   % reason)
      sys.exit(2)

    # Store the output as a class member so that any function can inspect the current state
    self.yaml_out = self.claimToYAML(claim)

    yaml.dump (self.yaml_out, yaml_file, default_flow_style = False, explicit_start = True)
    if self.yaml_out:
      return 0
    else:
      return 1

  def claimToYAML(self, claim):
    r = {}
    r['claimid'] = claim['userclaimid']
    r['reason'] = str(claim['reason'])
    r['user'] = str(claim['username'])
    r['requestdate'] = str(claim['requestdate'])
    r['grantdate'] = str(claim['grantdate'])
    r['returndate'] = str(claim['returndate'])
    
    resourceids, historic = self.ovtDB.getUserResources(claim['userclaimid'])

    r['resources'] = self.resourcesToYAML(claim['userclaimid'], resourceids)
    return r

  def resourcesToYAML(self, userclaimid, resourceids):
    r = {}
    for resourceid in resourceids:
      data = self.ovtDB.getUserResource(userclaimid, resourceid)
      r[str(data['type'])] = self.resourceToYAML(data)
    return r

  def resourceToYAML(self, data):
    r = {}
    r['name'] = str(data['name'])
    r['attributes'] = self.attributesToYAML(data['attributes'])
    r['requested'] = self.attributesToYAML(data['requested'])
    return r

  def attributesToYAML(self, data):
    r = {}
    for attribute in data:
      r[str(attribute)] = []
      for value in data[attribute]:
        r[str(attribute)].append(str(value))
    return r
 
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

