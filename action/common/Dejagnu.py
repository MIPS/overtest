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
from OvertestExceptions import *
from Config import CONFIG
# Support class for dejagnu based testsuites

class DejagnuCommon:

  def getCPU(self):
    """
    Determine which cpu this test is targetting
    """

    cpu = "meta"
    if self.version.find("mtx") != -1:
      cpu = "mtx"

    return cpu
  
  def getDejagnuCflags (self):
    """
    Format compiler flags for dejagnu runs
    """
    cflags = self.config.getVariable ("Compiler Flags")
    try:
      board = self.getResource ("Target Board")
      if board.getAttributeValue ("Core Revision") == "META122":
        cflags = "%s -mmetac=1.2" % cflags
      elif board.getAttributeValue ("Core Revision").startswith("META2"):
        cflags = "%s -mmetac=2.1" % cflags
    except (ResourceException, ConfigException):
      try:
        config = self.config.getVariable ("Simulator Config")
        if config == "122":
          cflags = "%s -mmetac=1.2" % cflags
        elif config in ['213','214','heron']:
          cflags = "%s -mmetac=2.1" % cflags
      except (ResourceException, ConfigException):
        None

    cflags = cflags.strip(" ")
    if cflags != "":
      cflags = "\\{%s\\}" % cflags.replace(" ", "\\ ")
    return cflags

  def setupDejagnuEnvironment(self, env, testsuiteSource, cpu):
    """
    Return an updated ENV for running dejagnu testsuites
    """ 

    env['METAG_INST_ROOT'] = self.config.getVariable ("METAG_INST_ROOT")

    # We need to use the gcc2 version of dejagnu as it is contains our config
    env['DEJAGNULIBS'] = os.path.join (testsuiteSource, "metag", "tools", "gcc2", "dejagnu")

    if not self.config.getVariable ("Execute Tests?"):
      env['METAG_NOEXECUTE'] = "1"

    if self.version.endswith(".sim"):
      # We are going to use the linux simulator
      env['METAG_FSIM_ROOT'] = self.config.getVariable ("METAG_FSIM_ROOT")
      # WORK NEEDED: Deprecate this
      env['FSIM_INST_ROOT'] = env['METAG_FSIM_ROOT']

      if cpu == "mtx":
        env['METAG_SIM'] = "mtx"
      else:
        env['METAG_SIM'] = self.config.getVariable ("Simulator Config");
    else:
      # Find out about the DA that has been allocated
      da = self.getResource ("Debug Adapter")
      env['DA_NAME'] = da.getAttributeValue ("DA Name")

    if not 'PATH' in env:
      env['PATH'] = "%s:%s" % (env['DEJAGNULIBS'],os.environ['PATH'])
    else:
      env['PATH'] = "%s:%s" % (env['DEJAGNULIBS'],env['PATH'])

    expect = self.neoSelect ("Expect", "5.45")

    if expect == None:
      self.error ("Unable to locate Expect component in neo")

    env['PATH'] = "%s:%s" % (os.path.join(expect, "bin"),env['PATH'])
    env['PATH'] = "%s:%s" % (os.path.join (sys.path[0], "addons", "simulator", "embedded"), env['PATH'])

    # Add the neo path
    env['PATH'] = CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo), env['PATH']])

    return env

