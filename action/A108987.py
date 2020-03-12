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
from common.Dejagnu import DejagnuCommon
from parsers.GCC4Regression import GCC4RegressionParser

# G++ Regression Suite

class A108987(Action, IMGAction, DejagnuCommon, GCC4RegressionParser):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108987
    self.name = "G++ Regression Suite"

  # Execute the action.
  def run(self):
    testsuiteSource = os.path.join (self.getWorkPath(), "source")
    testsuiteResults = os.path.join (self.getWorkPath(), "results")

    # Get the testsuite source
    result = self.neoGetSource (testsuiteSource, "Gcc2CompilerTestsuite",
                                                self.testrun.getVersion ("Gcc2CompilerTestsuite"))
    if not result:
      self.error ("Failed to fetch testsuite source")

    # Helper script for running the testsuite on an installed compiler
    test_installed = os.path.join (testsuiteSource, "metag", "tools", "gcc2", "contrib", "test_installed")
    
    # Determine the CPU from the version string
    cpu = self.getCPU ()

    # Create the correct environment based on the version string, variables and resources
    env = {}
    env = self.setupDejagnuEnvironment (env, testsuiteSource, cpu)

    # Find and format compiler flags for dejagnu
    cflags = self.getDejagnuCflags ()

    # Find the corba harness
    cpu_local_run = "%sg-local-run" % cpu

    # Run the testsuite
    result = self.execute(env=env, workdir=testsuiteResults,
                                   command=[test_installed, "--without-g77", "--without-objc", "--without-gcc",
                                            "--with-g++=%s" % os.path.join(env['METAG_INST_ROOT'], "bin", "%sg-local-g++"%cpu),
                                            "-target_board=%sg-sim%s" % (cpu,cflags), "SIM=%s" % cpu_local_run])

    # Save the log files
    self.registerLogFile (os.path.join (testsuiteResults, "g++.log"))
    self.registerLogFile (os.path.join (testsuiteResults, "g++.sum"))

    if result == 0:
      # Parse the g++ regression suite results
      summary = self.parse (os.path.join (testsuiteResults, "g++.log"))
      self.success (summary)

    return (result == 0)

