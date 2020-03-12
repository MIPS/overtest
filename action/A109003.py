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
from Action import Action
from IMGAction import IMGAction
from OvertestExceptions import *

# MetaMtxToolkit

class A109003(Action, IMGAction):
  def __init__ (self, data):
    Action.__init__(self, data)
    self.actionid = 109003
    self.name = "MetaMtxToolkit"

  # Execute the action.
  def run (self):
    # Ideally this action should verify the configuration
    toolkit_root = self.config.getVariable ("Manual Toolkit Root")
    METAG_INST_ROOT = None
    variant = None

    toolkit_build = self.config.getVariable("MetaMtxToolkit Build")
    if toolkit_build != "Any":
      variant = toolkit_build.split()[-1]

    if toolkit_root == "":
      asmexec_version = self.testrun.getVersion ("AsmExec")
      linkerexec_version = self.testrun.getVersion ("LinkerExec")
      ldlkexec_version = self.testrun.getVersion ("LdlkExec")
      tbicore_version = self.testrun.getVersion ("TbiCore")
      meoslib_version = self.testrun.getVersion ("MeOSLib")
      patched = False

      if variant == None:
        toolkit_spec = "%s/overtest.%u"%(self.version,self.testrunactionid)
        toolkit_root_spec = "%s/root"%(self.version)
      else:
        toolkit_spec = "%s:%s/overtest.%u"%(self.version,variant,self.testrunactionid)
        toolkit_root_spec = "%s:%s/root"%(self.version,variant)
      self.config.setVariable ("Toolkit Spec", toolkit_spec)

      if not self.testrun.isDefaultDependency(self.name, "AsmExec"):
        patched = True
        if not self.neoPatchToolkit (toolkit_spec, self.version, variant, \
                                     "AsmExec", asmexec_version):
          # Error is set by neoPatchToolkit
          return False
     
      if not self.testrun.isDefaultDependency(self.name, "LinkerExec"):
        patched = True
        if not self.neoPatchToolkit (toolkit_spec, self.version, variant, \
                                     "LinkerExec", linkerexec_version):
          # Error is set by neoPatchToolkit
          return False
     
      if not self.testrun.isDefaultDependency(self.name, "LdlkExec"):
        patched = True
        if not self.neoPatchToolkit (toolkit_spec, self.version, variant, \
                                     "LdlkExec", ldlkexec_version):
          # Error is set by neoPatchToolkit
          return False

      if tbicore_version != None and not self.testrun.isDefaultDependency(self.name, "TbiCore"):
        patched = True
        if not self.neoPatchToolkit (toolkit_spec, self.version, variant, \
                                     "TbiCore", tbicore_version, target_library=True):
          # Error is set by neoPatchToolkit
          return False

      if meoslib_version != None and not self.testrun.isDefaultDependency(self.name, "MeOSLib"):
        patched = True
        if not self.neoPatchToolkit (toolkit_spec, self.version, variant, \
                                     "MeOSLib", meoslib_version, target_library=True):
          # Error is set by neoPatchToolkit
          return False

      # Revert to the default 'root' area if nothing was patched. This saves space and
      # time when testing default tools. It also means tools do not have to be built
      # individually when the original version is being tested as they already exist in
      # the toolkit.
      if not patched:
        toolkit_spec=toolkit_root_spec
        self.config.setVariable ("Toolkit Spec", toolkit_spec)

      METAG_INST_ROOT = self.neoMetagInstRoot (toolkit_spec)
      if METAG_INST_ROOT is None:
        error ("Toolkit not found: %s" % toolkit_spec)
        
      self.registerLogFile (os.path.join (METAG_INST_ROOT, ".neo.txt")) 
    else:
      # Paths can be absolute and hence not be in neo. 
      if not toolkit_root.startswith(os.sep):
        if variant == None:
          toolkit_spec="%s/%s" % (self.version, toolkit_root)
        else:
          toolkit_spec="%s:%s/%s" % (self.version, variant, toolkit_root)

        self.config.setVariable ("Toolkit Spec", toolkit_spec)
        METAG_INST_ROOT = self.neoMetagInstRoot (toolkit_spec)
        if METAG_INST_ROOT == None:
          self.error("Unable to find METAG_INST_ROOT for %s" % (toolkit_spec))
        self.registerLogFile (os.path.join (METAG_INST_ROOT, ".neo.txt")) 
      else:
        self.config.setVariable ("Toolkit Spec", "scratch")
        METAG_INST_ROOT = toolkit_root

    self.config.setVariable ("METAG_INST_ROOT", METAG_INST_ROOT)
    return True

  def archive(self):
    # Ignore any config or resource errors. If there are errors then this code is probably not applicable
    # to the given instance anyway. (Fail during run or not run for example).
    try:
      if self.config.getVariable ("Manual Toolkit Root") == "" and \
         self.config.getVariable ("Toolkit Spec") != "scratch" and \
         not self.config.getVariable ("Toolkit Spec").endswith("/root"):
        toolkit_spec = self.config.getVariable ("Toolkit Spec")
        if toolkit_spec != "":
          self.execute(command=["rm", "-rf", self.neoMetagInstRoot (toolkit_spec)])
    except (ResourceException, ConfigException), e:
      None
