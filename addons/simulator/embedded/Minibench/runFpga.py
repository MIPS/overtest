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
  
 
