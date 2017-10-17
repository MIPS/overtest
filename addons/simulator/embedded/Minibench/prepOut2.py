#*****************************************************************************
#
#               file : $RCSfile: prepOut2.py,v $
#             author : $Author: rst $
#  date last revised : $Date: 2012/02/09 17:46:32 $
#    current version : $Revision: 1.2 $
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
#        description : Meta MiniBench prepOut2; generates a startup script for
#                      the VHDL testbench
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

  # Out2 script defaults to 2500 polls for end of test; override with METAT_OUT2_POLLCOUNT value if def'd
  out2polls = int(2500)
  for key in keys:
    if search("METAT_OUT2_POLLCOUNT", key):
      out2polls = int(os.environ['METAT_OUT2_POLLCOUNT'])
      if verbose == 1 :
        print "runSim: Out2 end-of-test pollcount set to %d" %out2polls

  # Pick up the threads mask from ldrout.py
  import ldrout
  threadsmask = long(ldrout.ThreadsMask(),16)

  # Start the out2 script
  import preout2
  preout2.initOut2(threads, threadsmask, perftest, verbose)

  import Microbench

  # Setup Microbench with options for MTX and reporting TestProgress to console
  Microbench.SetupMb(verbose, mtx)

  # Set up and load memories in use for this test
  import MemorySetup
  MemorySetup.SetupMemory(Microbench)

  # Run threads, poll for completion and check end state
  Microbench.RunThreads(threads, threadsmask, 0, out2polls)

  print "\nGenerated out2.txt scripts \n"

  exit (0)

# End of prepOut2.py
