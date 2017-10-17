import sys
import os
import getopt
import OvtDB
from OvertestExceptions import *

class NotifyExporter:
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
    print "Usage: (no options)"
    sys.exit (exitcode)

  def exportData(self, args):
    if len(args) != 0:
      self.usage(1)

    userinfo = sorted(OvtDB.OvtDBUser.find(self.ovtDB),
                      key=lambda x: x.name)
    print "my %user_table = ("
    print "# 'user'     => { growl => [ 'hostname',   'growl-password' ],"
    print "#                 mail  => [ 'email address' ],"
    print "#               },"

    for user in userinfo:
      for name in user.altnames.split(","):
        print "'%s' => {" % name
        if user.growlhost != None:
          print "growl => [ '%s', '%s' ]," % (user.growlhost, user.growlpassword.replace("\\","\\\\").replace("'","\\'"))
        if user.email != None:
          print "mail  => [ '%s %s', '%s' ]," % (user.fname, user.sname, user.email)
        print "},"
    print ");"

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

