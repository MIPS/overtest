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
import sys
from sys import path


if __name__ == "__main__" :
  
  sys.path.append(os.getcwd())

  import preout2
  
  preout2.initOut2(int(sys.argv[3]))

  import FPGA
  
  # Setup the Dash

  FPGA.InitTarget(sys.argv[1], sys.argv[2])
  
  import Minibench
  
  # Setup Minibench with FPGA target and option to generate out2.txt
  Minibench.SetupMb(FPGA, 1)

  #run FPGA test through ldrout.py
  
  import ldrout
  
  # Now execute ldrout.py functions
  ldrout.LoadDnl(None)
  
  ldrout.ConfigRegs()
  
  ldrout.SetThreads()
  
  # Setup start state MemDump with library module and thread state(0-start state and 1-end state)
  MemorySetup.SetupMemDump(Minibench, 0)

  Minibench.RegDump2out2(threads, 0)

  ldrout.StartThreads()
  
  ldrout.PollforTestEnd()

  Minibench.RegDump2out2(threads, 1)

  # Setup end state MemDump with library module and thread state(0-start state and 1-end state)
  MemorySetup.SetupMemDump(Minibench, 1)
  
  FPGA.stopTarget()
  
  print "\n Run on FPGA successful \n"
  
 
