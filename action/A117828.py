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
from Config import CONFIG

# Codesize

class A117828(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117828
    self.name = "Codesize"

  # Execute the action.
  def run(self):
    # Execute a command overriding some environment variables
    result = self.execute(workdir=self.getSharedPath(),
                          command=[CONFIG.git, "clone",
                                               "--reference=%s/uTest.git" % CONFIG.gitref,
                                               "git://mipssw-mgmt.ba.imgtec.org/sec/uTest.git",
                                               "uTest"])

    if result != 0:
      self.error("Unable to clone uTest repository")


    result = self.execute(workdir=os.path.join(self.getSharedPath(), "uTest"),
                          command=[CONFIG.git, "checkout", "overtest"])

    if result != 0:
      self.error("Unable to checkout uTest branch")
 
    result = self.execute(workdir=self.getSharedPath(),
                          command=[CONFIG.git, "clone",
                                               "--reference=%s/codesize-test-suites.git" % CONFIG.gitref,
                                               "git://mipssw-mgmt.ba.imgtec.org/sec/codesize-test-suites.git",
                                               "codesize-test-suites"])

    if result != 0:
      self.error("Unable to clone codesize-test-suites repository")

    result = self.execute(workdir=os.path.join(self.getSharedPath(), "codesize-test-suites"),
                          command=[CONFIG.git, "checkout", "overtest"])

    if result != 0:
      self.error("Unable to checkout codesize-test-suites branch")

    env = { 'PATH' : CONFIG.makeSearchPath([os.path.join(self.getSharedPath(), "uTest"),
                                            CONFIG.getProgramDir(CONFIG.python),
                                            os.environ['PATH']]) }

    triple = self.config.getVariable("Triple")
    vendor = triple.split("-", 2)[1]
    osname = triple.split("-", 2)[2]
    cflags = self.config.getVariable("CFLAGS")
    toolchain_root = self.config.getVariable("Toolchain Root")

    config_text = ("include overtest\n"
		   "\n"
		   "config mips_toolchain inherits " + vendor + ",os:" + osname + "\n"
                   "{\n"
                   "  path = " + os.path.join(toolchain_root, "bin") + "\n"
		   "}\n"
		   "\n"
                   "config mips_gcc_options\n"
                   "{\n"
                   "  cmd_line += " + cflags + "\n"
                   "}\n"
		   "\n"
	           "variation mips_toolchains is mips_toolchain\n"
	           "variation mips_gcc_options is mips_gcc_options\n")

    config_file = open(os.path.join(self.getSharedPath(),
                                    "codesize-test-suites",
				    "testsuites",
				    "config.tst"), "w")

    config_file.write(config_text)
    config_file.close()

    result = self.execute(workdir=os.path.join(self.getSharedPath(),
	                                       "codesize-test-suites",
					       "testsuites"),
			  env=env,
			  command=["%s -t%s -Rcodesize -Afunc_size,stderr -Tfunc_size"
				   % (os.path.join(self.getSharedPath(),
                                                   "codesize-test-suites",
			                           "scripts",
					           "codesize"),
				      self.concurrency)],
			  shell=True)

    testsuites_dir = os.path.join(self.getSharedPath(),
				  "codesize-test-suites",
				  "testsuites")
    logfile = open(os.path.join(testsuites_dir,
				"codesize_func_size_total.csv"))
			 

    totalsize = 0

    logfile.readline()
    for total in logfile:
      (testname,size) = total.split(",")
      testname = testname.strip()
      if size.strip() == "":
	size = 0
      else:
	size = int(size.strip())
      totalsize += size
      self.testsuiteSubmit(testname, True, {"size": size})
    logfile.close()

    for logfile in ["codesize_func_size_all.csv",
		    "codesize_func_size_total.csv",
		    "codesize_stderr_all.csv"]:
      self.registerLogFile (os.path.join (testsuites_dir,logfile), True)

    return self.success({"size": totalsize, "failures":result != 0})
