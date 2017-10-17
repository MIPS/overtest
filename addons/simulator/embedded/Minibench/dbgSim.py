#*****************************************************************************
#
#               file : $RCSfile: dbgSim.py,v $
#             author : $Author: rst $
#  date last revised : $Date: 2012/06/13 14:03:30 $
#    current version : $Revision: 1.18 $
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
#        description : Meta MiniBench dbgSim; allows testing of debugger scripts
#                      interaction with the simulator, based on runSim.py
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


# Maximum number of threads we expect to handle
maxthreads = 4

# Dummy class for timeouts
class TimeoutException(Exception) :
  pass 

# Wrap ldrout.PollforTestEnd in some timeout logic
# Returns 0 if completed, 1 if timed out
def PollforTestEnd(polltimeout):

  # Define our timeout handler
  def timeout_handler(signum, frame):
    raise TimeoutException()

  polltimedout = 0

  if verbose == 1 :
    print "\n\tdbgSim PollforTestEnd with %d secs left" %polltimeout
  
  if platform.system() != "Windows":
    # Vector our timeout handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)

    # Set our timeout
    signal.alarm(polltimeout)
  else:
    # On windows signal.alarm is not available, therefore timeout feature
    # currently not available.
    print "dbgSim: Timeout feature disabled on windows."

  try:
    ldrout.PollforTestEnd()
  except TimeoutException :
    if verbose == 1 :
      print "\ndbgSim PollforTestEnd: Timed out"
    polltimedout = 1
  finally:
    if platform.system() != "Windows":
      # Restore timeout handler
      signal.signal(signal.SIGALRM, old_handler)

  if platform.system() != "Windows":
    # Reset python's timer
    signal.alarm(0)

  return polltimedout


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

  # Assume InSimStart/Stop logging unless we see the forceinsimlog option
  forceinsimlog = 0

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
    if o == "--forceinsimlog" :
      forceinsimlog = 1
    if o == "--mtx":
      mtx = 1
    if o == "--perftest":
      perftest = 1

  # Timeout (60 secs)
  # Need to override via command line with METAT_ONETEST_TIMEOUT value if def'd
  timeout = int(60)
  for key in keys:
    if search("METAT_ONETEST_TIMEOUT", key):
      timeout = int(os.environ['METAT_ONETEST_TIMEOUT'])
      if verbose == 1 :
        print "dbgSim: Test timeout set to %d secs" %timeout

  # Assume no threads
  threadsmask = 0

  # See if the test provided an executable
  if os.path.exists("ldrout.py") :
    if verbose == 1 :
      print "\ndbgSim: sourcing test executable"
    import ldrout

    # Pick up the threads mask
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

  dcache_size = Minibench.DCacheGetSize()

  # Set up memories in use for this test
  import MemorySetup
  MemorySetup.SetupMemory(Minibench)

  # If we've got an executable, just load it up and dump
  # the starting state - test script should start it
  if threadsmask != 0 :
    ldrout.LoadDnl(None)
    MemorySetup.MemDump(Minibench, 0)

  # Somewhere to store the queried states
  tstates = [0]*maxthreads

  # Need to check how long this all takes
  starttime = int(time.time())

  # Cause the CSim to execute a bit...
  CSim.Execute(pMetac, 1000)

  # Run the dbgif script..
  if verbose == 1 :
    print "\ndbgSim: Running debug script.."
  import dbgsim
  dbgsim.dbgSim(verbose, pMetac)

  runtime = int(time.time()) - starttime

  # If we've got an executable, make sure it halted properly
  if threadsmask != 0 :
    timedout = PollforTestEnd(timeout-runtime)
  else :
    timedout = 0

  # Expect the test script to have halted threads
  # just make sure we didn't take too long
#  runtime = int(time.time()) - starttime
#  if runtime >= timeout :
#    timedout = 1
#    if verbose == 1 :
#      print "\ndbgSim: Test run timed out after %d secs" %runtime

    if timedout == 0 :
      if verbose == 1 :
        print "\ndbgSim: Test endpoint reached after %d secs; dumping end state" %runtime
      Minibench.DCacheFlush(dcache_size, 0)
      MemorySetup.MemDump(Minibench, 1)

    else :
      if verbose == 1 :
        print "\ndbgSim: Poll for Test End timed out after %d secs" %runtime


  # Stop the Simulator
  retval = CSim.SimStop(pMetac)

  if timedout == 0 :

    if verbose == 1 :
      print "\ndbgSim: Test completed after %d secs" %runtime
    else :
      print "\n"

    if retval == 0 :
      print "Run on Simulator successful \n"
    else:
      print "Run on Simulator failed. Return value: %d\n" %retval

  else:
    print "\n Run on Simulator timed out\n"
    retval = -1

  exit (retval)

# End of dbgSim.py
