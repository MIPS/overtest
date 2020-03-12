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
from action.Action import Action
from action.IMGAction import IMGAction
from OvertestExceptions import ResourceException

class VerificationSuiteAction(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)

  def group_option(self):
    g = self.groups()
    if g == None:
      return None
    else:
      return str(','.join(g))

  def groups(self):
    return None

  def tests_option(self):
    t = self.tests()
    if t == None:
      return None
    else:
      assert len(t) == 1
      return str(','.join(t))

  def tests(self):
    return None

  def verify_version(self):
    return '.'.join(self.version.split('.')[0:4])

  def verify_template(self):
    return "verify"

  def tools_option(self):
    return str(self.testrun.getVersion("MetaMtxToolkit"))

  def post_process(self):
    return self.success()

  # Execute the action.
  def run(self):
    kwargs = { 'TOOLS' : self.tools_option(),
               'GROUP' : self.group_option(),
               'JUSTONE' : self.tests_option(),
               'VERIFY'  : self.verify_version(),
               'template' : self.verify_template()
             }

    for k, v in kwargs.items():
      if v == None:
        del kwargs[k]

    env = { 'VERBOSE' : '2' }

    try:
      DA = self.getResource("Debug Adapter")
    except ResourceException, e:
      pass
    else:
      DA_NAME = DA.getAttributeValue("DA Name")
      env['METAT_USE_TARGET'] = DA_NAME

    if self.testrun.getVersion("MECCToolkit") != None:
      env['MECC_INST_ROOT'] = self.config.getVariable ("MECC_INST_ROOT")
      env['LM_LICENSE_FILE'] = os.path.join(os.path.expanduser("~"), "licenses", "uncounted.lic")
      kwargs['COMPILER'] = "mecc"

    result = self.neoVerify(env=env, **kwargs)

    if not result == 0:
      self.error ("Failed to run command")
    return self.post_process()
