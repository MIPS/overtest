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
import hashlib
import re
import os
import shlex
import glob
from utils.Utilities import versionCompare
from Action import Action
from common.EEMBC import EEMBCAction

# BuildEEMBC

def md5_for_file(f, block_size=2**20):
  md5 = hashlib.md5()
  while True:
    data = f.read(block_size)
    if not data:
      break
    md5.update(data)
  return md5.hexdigest()

class A113830(Action, EEMBCAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 113830
    self.name = "BuildEEMBC"

  # Execute the action.
  def run(self):
    cqstat_out = self.getWorkPath ()

    metag_inst_root = self.config.getVariable ("METAG_INST_ROOT")
    workdir         = self.config.getVariable ("EEMBC Source")
    toolchain       = "metagcc"
    platform_family = self.version.split(".")[-1]
    config          = self.config.getVariable ("EEMBC Config %s"%platform_family)
    cq_stat         = self.config.getVariable ("EEMBC CQStat")
    benchmark       = self.config.getVariable ("EEMBC Benchmarks")
    uuencode        = self.config.getVariable ("EEMBC UUENCODE")
    extra           = shlex.split (self.config.getVariable ("EEMBC Arbitrary"))

    platform = "%s%s"%(platform_family,config)
    self.config.setVariable ("EEMBC Platform", platform)

    env = { 'METAG_INST_ROOT' : metag_inst_root,
            'ALLOW_REMOTE_HASP' : '1'
          } 

    if self.testrun.getVersion("MECCToolkit") != None:
      mecc_inst_root = self.config.getVariable ("MECC_INST_ROOT")
      env['MECC_INST_ROOT'] = mecc_inst_root
      env['LM_LICENSE_FILE'] = os.path.join(os.path.expanduser("~"), "licenses", "uncounted.lic")
      toolchain = "metamecc"

    cmd = ["scripts/build.sh"]
    cmd.extend (["--toolchains", toolchain])
    cmd.extend (["--platforms",  platform])
    if cq_stat == 1:
      cmd.append ("--cq-stat")
      cmd.extend (["--cq-stat-output", cqstat_out])
      #cqstat_out = "%s/CodeQuality"%workdir # TODO: Remove
      if not self.createDirectory (cqstat_out):
        return False
      self.config.setVariable ("EEMBC CQStat Output", cqstat_out)
    cmd.extend (["--harnesses", "th_lite"])
    cmd.extend (["--benchmarks", benchmark])
    if uuencode != 1:
      cmd.append ("--no-uuencode")

    implementation  = self.config.getVariable ("EEMBC %s Implementation"%platform_family)
    self.config.setVariable ("EEMBC Implementation", implementation)
    if len(implementation) > 0:
      cmd.extend (["--implementation", implementation])

    added_dashdash = False
    if len(extra) > 0:
      cmd.append ("--")
      cmd.extend (extra)
      added_dashdash = True

    xcflags = self.config.getVariable ("EEMBC XCFLAGS")
    xlflags = self.config.getVariable ("EEMBC XLFLAGS")
    xiflags = self.config.getVariable ("EEMBC XIFLAGS")
    if len(xcflags) > 0:
      if not added_dashdash:
        cmd.append ("--")
        added_dashdash = True
      cmd.extend (["METAG_EEMBC_XCFLAGS=%s" % xcflags])
    if len(xlflags) > 0:
      if not added_dashdash:
        cmd.append ("--")
        added_dashdash = True
      cmd.extend (["METAG_EEMBC_XLFLAGS=%s" % xlflags])
    if len(xiflags) > 0:
      if not added_dashdash:
        cmd.append ("--")
        added_dashdash = True
      cmd.extend (["METAG_EEMBC_XIFLAGS=%s" % xiflags])

    build_result = self.execute (command=cmd, env=env,
                                 workdir="%s/eembc"%workdir)

    bmarks = self.fetchBmarkList(workdir, platform)
    if bmarks == False:
      # Error set by fetchBmarkList
      return False

    anything_passed = False
    bin_dir = "%s/eembc/%s/%s/bin_lite" % (workdir, benchmark, toolchain)

    for bmark in bmarks:
      passed = False
      extendedresults = {}

      ldlk_bin = os.path.join (bin_dir, "%s_lite_t0.elf" % bmark)
      if os.path.exists (ldlk_bin):
        extendedresults['LDLK MD5'] = md5_for_file (open (ldlk_bin))
        passed = True
        anything_passed = True

      ld_bin = os.path.join (bin_dir, "%s_lite.elf" % bmark)
      if os.path.exists (ld_bin):
        extendedresults['LD MD5'] = md5_for_file (open (ld_bin))

      self.testsuiteSubmit (bmark, passed,
                            extendedresults=extendedresults)

    if build_result != 0:
      self.error ("Failed to build EEMBC")

    if not anything_passed:
      self.error ("Nothing built")
    
    return True
