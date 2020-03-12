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
import os
from Config import CONFIG
from Action import Action
from IMGAction import IMGAction
from Perforce import PerforceConnection

# Fetch

class A115850(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 115850
    self.name = "Fetch"

  # Execute the action.
  def run(self):
    sharedir = self.getSharedPath()

    do_apps = self.config.getVariable ("RA Do Apps").split(",")
    self.config.setVariable ("RA_SOURCE", sharedir)

    host = self.getResource("Execution Host")
    p4port = str(host.getAttributeValue('P4PORT'))
    p4user = str(host.getAttributeValue('P4USER'))

    env = {
            'PATH' : CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo),
                                            CONFIG.getProgramDir(CONFIG.perl),
                                            os.environ['PATH']]),
            'P4USER' : p4user,
            'P4PORT' : p4port
          }

    fetch_options = []

    if self.version.startswith('CHANGELIST'):
      changelist = self.config.getVariable('RA_FETCH_CHANGELIST')
      if not changelist.startswith("@"):
        changelist = "@%s" % str(changelist)
      fetch_options.append("--changeset=%s" % changelist)
      fetch_options.append("--location=//meta/swcore/code/" +\
                           "regressionapps/MAIN/metag/" +\
                           "regressionapps/xyRegressionApps.xyf")
      fetch_options.append("RegressionApps")
    else:
      fetch_options.append("RegressionApps:%s" % self.version)

    p4_cmp = self.config.getVariable("COBIT_INST_ROOT")
    p4_cmp = os.path.join(p4_cmp, "bin", "p4_cmp")

    command = [p4_cmp, "fetch", "--writable"]
    fw_command = command[:]
    fw_command.append("--partial=metag/regressionapps/framework/...")
    fw_command.extend(fetch_options)
    fw_command.append(sharedir)
    print fw_command

    # Fetch the framework
    result = self.execute (env=env, command=fw_command)
    if result != 0:
      self.error("Unable to fetch framework")

    result = self.execute (env=env,
                           command=["./dependencies.pl"] + do_apps,
                           workdir=os.path.join(sharedir, 'metag', 
                                                'regressionapps',
                                                'framework', 'performance'))
    if result != 0:
      self.error ("Could not fetch dependencies")

    deps = set()
    for dep in self.fetchOutput().split("\n"):
      if dep != "":
        name = self.findComponentToCheckout(dep)
        deps.add(name)

    for subpath in deps:
      sub_command = command[:]
      sub_command.append("--partial=%s" % subpath)
      sub_command.extend(fetch_options)
      sub_command.append(sharedir)

      result = self.execute (env=env, command=sub_command)
      if result != 0:
        self.error("Unable to fetch %s" % subpath )

    return True

  def findComponentToCheckout(self, name):
    parts = name.split('/')

    # Cannot handle partial checkout
    component_name = parts[0]

    cmps = { 'StandardRegressionApps'   : 'metag/regressionapps/standard/...',
             'AdditionalRegressionApps' : 'metag/regressionapps/additional/...',
           }

    if component_name not in cmps:
      self.error("Unknown sub-component found: %d" % component_name)

    return cmps[component_name]
