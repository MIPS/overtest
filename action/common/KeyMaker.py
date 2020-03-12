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

class KeyMaker:
  """
  Generates MD5 keys
  """
  def getVerifyMD5Keys(self, directory, type, info_on=0):

    if type == "static":
      style = "ST"
    elif type == "FPGA":
      style = "FP"
    else:
      self.error("Unknown build type: %s\n", type)
      
    verifyMD5Keys = {}
    for root, dirs, files in os.walk(directory):
      # Get the keymaker
      for file in files:
        if not file.endswith(".tgz"):
          continue
        # Now see if this is a non-standard style:
        res = self.execute(command=["tar", "-O", "-xzf", os.path.join(root, file), "%s/runtype.txt" % (file[:-4])])
        if res != 0:
          self.proccount -= 1
          continue
        
        runtype = self.fetchOutput().strip().rstrip("\n")
        self.proccount -= 1
        
        newstyle=style
        if runtype == "RUNTYPE=NSIM":
          newstyle="NS"
        elif runtype == "RUNTYPE=STATIC-SIM":
          newstyle="ST"
        elif runtype == "RUNTYPE=INSCRIPT":
          newstyle="IN"
        elif runtype == "RUNTYPE=FPGA":
          newstyle="FP"

        key = self.neoKeyMaker(os.path.join(root, file), newstyle, info_on)
        if key != None:
          verifyMD5Keys[file[:-4]] = key

    return verifyMD5Keys
