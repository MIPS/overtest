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

