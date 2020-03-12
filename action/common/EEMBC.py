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
class EEMBCAction:
  """
  Common functionality for EEMBC Build and Run stages
  """
  def fetchBmarkList(self, workdir, platform):
    """
    Fetch a list of benchmarks that will run based on the platform
    """
    bmarks_mk = ("include consumer_lite/dirsv2%s.mak" % platform) +\
                "\n" +\
                "all:\n" +\
                "\t@echo $(bmarks)\n"

    bmarks_mkfile = open("%s/eembc/bmark.mk" % workdir, "w")
    bmarks_mkfile.write(bmarks_mk)
    bmarks_mkfile.close()

    result = self.execute (command=["make", "-f", "bmark.mk"],
                           workdir="%s/eembc" % workdir)

    if result != 0:
      self.error ("Failed to determine bmark list")

    bmarks = self.fetchOutput()
    return bmarks.strip().split(" ")
