#*****************************************************************************
#
#               file : $RCSfile: loadSim.py,v $
#             author : $Author: rst $
#  date last revised : $Date: 2012/01/26 14:47:29 $
#    current version : $Revision: 1.4 $
#
#          copyright : 2010 by Imagination Technologies.
#                      All rights reserved.
#                      No part of this software, either material or conceptual
#                      may be copied or distributed, transmitted, transcribed,
#                      stored in a retrieval system or translated into any
#                      human or computer language in any form by any means,
#                      electronic, mechanical, manual or otherwise, or
#                      disclosed to third parties without the express written
#                      permission of:
#                        Imagination Technologies, Home Park Estate,
#                        Kings Langley, Hertfordshire, WD4 8LZ, U.K.
#
#        description : Meta MiniBench loadSim; loads an executable into
#                      CSim and generates a starting state for the VHDL
#                      testbench for the 'nodiff' version of dbgSim
#
#            defines :
#
#****************************************************************************

import os
import sys
from sys import path
import time
import signal
import shutil
import getopt
import textwrap
import platform


# Check for command line arguments
if __name__ == "__main__" :
  # Cmd Line args Processing 

  sys.path.append(os.getcwd())
  
  try:
    opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "regdef=",
                                                           "ignorefile=",
														   "paramdir=",
														   "bmpdir=",
														   "objanal=",
														   "fo=",
														   "fw=",
														   "fi=",
														   "mtx",
														   "insimtest",
														   "quiet",
														   "forceinsimlog",
														   "linestorewidth=",
														   "perftest",
														   "rc="])

  except getopt.GetoptError, err:
    print "Usage Error: " + str(err)
    sys.exit(2)

  keys = os.environ.keys()
  
  from re import search
  
  for key in keys:
    if not search("METACNAME", key):
      os.environ["METACNAME"]="test"

  # Assume verbose logging unless we see the quiet option
  verbose = 1

  # Assume not MTX to start with
  mtx = 0

  # Assume we don't need special setup for a performance test
  perftest = 0

  # Pick up options we are interested in
  for (o,a) in opts:
    if o == "--rc" :
      threads = int(a)
    if o == "--quiet" :
      verbose = 0
    if o == "--mtx":
      mtx = 1
    if o == "--perftest":
      perftest = 1

  # Pick up the threads mask from ldrout.py
  import ldrout
  threadsmask = long(ldrout.ThreadsMask(),16)

  # Start the out2 script
  import preout2
  preout2.initOut2(threads, threadsmask, perftest, verbose)

  import CSim

  # Start the Simulator
  pMetac = CSim.SimStart(opts, args, None)

  import Minibench

  # Setup Minibench to write with Csim target, and option to report TestProgress to console
  Minibench.SetupMb(CSim, verbose, mtx)

  # Set up memories in use for this test
  import MemorySetup
  MemorySetup.SetupMemory(Minibench)

  # Load up the executable and dump the starting state
  import ldrout
  ldrout.LoadDnl(None)
  MemorySetup.MemDump(Minibench, 0)

  # Stop the Simulator
  retval = CSim.SimStop(pMetac)

  print "\nSimulator image dumped\n"

  exit (retval)

# End of loadSim.py
