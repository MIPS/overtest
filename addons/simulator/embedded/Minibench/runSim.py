#*****************************************************************************
#
#               file : $RCSfile: runSim.py,v $
#             author : $Author: anb $
#  date last revised : $Date: 2012/12/14 16:53:12 $
#    current version : $Revision: 1.3 $
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
#        description : Meta MiniBench
#
#            defines :
#
#****************************************************************************

import os
import sys
from sys import path
import os.path
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

def ExecuteCheckEvents (pMetac, Cycles) :
  CSim.Execute (pMetac, Cycles)
  CSimStatus = CSim.QueryStatus (pMetac)
  if CSimStatus != 0x0 : 
    print 'QueryStatus: ' + str (CSimStatus)
  if CSimStatus == 0x1 :
    CSim.HandleEvent (pMetac)

# Wrap ldrout.PollforTestEnd in some timeout logic
# Returns 0 if completed, 1 if timed out
def PollforTestEnd(polltimeout):

  # Define our timeout handler
  def timeout_handler(signum, frame):
    raise TimeoutException()

  polltimedout = 0

  if verbose == 2 :
    print "\n\trunSim PollforTestEnd with %d secs left" %polltimeout
  
  if platform.system() != "Windows":
    # Vector our timeout handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)

    # Set our timeout
    signal.alarm(polltimeout)
  else:
    # On windows signal.alarm is not available, therefore timeout feature
    # currently not available.
    print "runSim: Timeout feature disabled on windows."

  try:
    ldrout.PollforTestEnd()
  except TimeoutException :
    if verbose == 2 :
      print "\nrunSim PollforTestEnd: Timed out"
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
                                                           "insimlogend",
                                                           "transaction",
                                                           "timing=",
                                                           "startintrusive",
                                                           "linestorewidth=",
                                                           "perftest",
                                                           "rc="])

  except getopt.GetoptError, err:
    print "Usage Error: " + str(err)
    sys.exit(2)

  from re import search
  
  if 'METACNAME' not in os.environ:
    os.environ["METACNAME"]="test"

  # Assume verbose logging unless we see the quiet option
  verbose = 1

  # Assume logging starts at InSimStartEvt() unless we see the forceinsimlog option
  forceinsimlog = 0

  # Assume logging stops at InSimStopEvt() unless we see the insimlogend option
  insimlogend = 0

  # Assume we don't start threads with the intrusive bit unless we see the startintrusive option
  start_intrusive = 0

  # Assume not MTX to start with
  mtx = 0

  # Assume we run the simulator in normal mode, we could choose to run in transaction mode
  transaction = 0

  # Assume we don't need special setup for a performance test
  perftest = 0

  # Assume we run the simulator in normal mode, we could choose to run in event synchronisation mode
  SyncFileName = None
  SyncTiming=0
  SyncFile = None
  
  # Default running cycles for normal mode will be 100000, 
  # but for transaction mode the running cycles will be 1000
  exeCycles = 100000

  # Pick up options we are interested in
  for (o,a) in opts:
    if o == "--rc" :
      threads = int(a)
    if o == "--quiet" :
      verbose = 0
    if o == "--forceinsimlog" :
      forceinsimlog = 1
    if o == "--insimlogend" :
      insimlogend = 1
    if o == "--startintrusive" :
      start_intrusive = 1
    if o == "--mtx":
      mtx = 1
    if o == "--transaction":
      transaction = 1
    if o == "--perftest":
      perftest = 1
    if o == "--timing" :
        SyncFileName=str(a)
        SyncTiming = 1

  if transaction == 1 :
    exeCycles = 1000
    if verbose == 1:
      print "Running simulator in transaction mode, execution cycles will be %d" %exeCycles
  else :
    if verbose == 1:
      print "Running simulator in normal mode, execution cycles will be %d" %exeCycles

  if SyncTiming == 1 :
    exeCycles = 1
    if verbose == 1:
      print "Running simulator in event synchronisation mode, file name: %s Cycle:%d" %(SyncFileName, exeCycles)

  # Timeout defaults to 60 secs, or override with METAT_ONETEST_TIMEOUT value if def'd
  timeout = 60
  if 'METAT_ONETEST_TIMEOUT' in os.environ:
    timeout = int(os.environ['METAT_ONETEST_TIMEOUT'])
    if verbose == 1 :
      print "runSim: Test timeout set to %d secs" %timeout

  # Out2 script defaults to 2500 polls for end of test; override with METAT_OUT2_POLLCOUNT value if def'd
  out2polls = int(2500)
  if 'METAT_OUT2_POLLCOUNT' in os.environ:
    out2polls = int(os.environ['METAT_OUT2_POLLCOUNT'])
    if verbose == 1 :
      print "runSim: Out2 end-of-test pollcount set to %d" %out2polls

  # Pick up the threads mask from ldrout.py
  import ldrout
  threadsmask = long(ldrout.ThreadsMask(),16)

  # Start the out2 script
  import preout2
  preout2.initOut2(threads, threadsmask, perftest, verbose)

  import CSim

  # Start the Simulator
  pMetac = CSim.SimStart(opts, args, None)

  if verbose == 1:
    print 'Using Meta C Simulator Version: ' + CSim.GetSimVersion()

  if SyncTiming == 1 :
    SyncFile=open(SyncFileName, "r")

  import Minibench

  # Setup Minibench to write with Csim target, and option to report TestProgress to console
  Minibench.SetupMb(CSim, verbose, mtx)

  dcache_size = Minibench.DCacheGetSize()

  # Set up memories in use for this test
  import MemorySetup
  MemorySetup.SetupMemory(Minibench)

  # Now execute ldrout.py functions

  ldrout.LoadDnl(None)

  ldrout.ConfigRegs()

  ldrout.SetThreads()

  # Somewhere to store the queried states
  tstates = [0]*maxthreads

  starttime = int(time.time())
  runtime = 0
  lasttime = 0
  timedout = 0

  # Set initial CSim status
  Status = 0xDEADBEEF

  # For conventional runs, get things running and look for InSimStartEvt before we dump start state
  if forceinsimlog == 0 :

    CSim.AckLogEvent(pMetac)

    if verbose == 2 :
      print "\nrunSim: Starting thread(s) from reset"
      # Running from boot, just get it going
    ldrout.StartThreads()

    # Initialise thread start cycle for each thread, since vhdl start logging from
    # InSimStartEvt, so we need to add previous instruction to cycle count
    CSim.InitThreadStartCycle(pMetac, verbose)

    # indicate that whether we could put more events into event queue
    bFull = 0

    # This is the preprocessing stage, before we start executing any instructions
    # we need to read in synchronisation events
    if SyncFile is not None :
      # We will get as many events as we can to put them into the queue first
      # If the queue is full, then we won't process new line from the syncfile
      # we will keep the current line, until it is processed
      while bFull == 0 and SyncFile is not None :
        eventLine = SyncFile.readline()

        # If we reach the end of the sync file, we will close it
        if len(eventLine) == 0 : 
          SyncFile.close()
          SyncFile=None
        # If the event queue is full, then we can start executing instructions
        # Until there is empty slot in the queue, then we can process new event
        else :
          bFull = CSim.EventSync(pMetac, eventLine, threads, verbose)

    if insimlogend == 0 :
        # Wait until all running threads report that they have reach log end point.
        # Loop exits via 1 of 2 breaks tested within the loop
      all_disabled = 0

      while 1 :
        # We will close SyncFile, after we process all events, so here we
        # will check whether SyncFile is closed
        if SyncFile is not None :
          # If the event queue is full, we will keep polling and keep previous
          # unhandled record, until there is empty slot in the queue
          # when queue is full, bFull will be set and eventLine won't be changed
          if bFull == 0 :
            eventLine = SyncFile.readline()
            
          if len(eventLine) == 0 :
            SyncFile.close()
            SyncFile=None
          else :
            bFull = CSim.EventSync(pMetac, eventLine, threads, verbose)

        # Cause the CSim to execute a bit...
        ExecuteCheckEvents (pMetac, exeCycles)

        # Now check to see if we have reached end of logging on all threads.
        for thread in range(0, maxthreads) :
          tstates[thread] = CSim.QueryThreadState(pMetac, thread)
          if tstates[thread] != 0x1:
            all_disabled = 0
          else:
            all_disabled = 1
          
        if all_disabled == 1:
          break

        # test that all threads are ready...
        if tstates.count(4) == threads :
          break

        # Test for timeout
        runtime = int(time.time()) - starttime
        if runtime >= timeout :
          timedout = 1

          if verbose == 2 :
           print "\nrunSim: Test run timed out after %d secs" %runtime
           break
          else :
            if ( (verbose == 2) and (lasttime != runtime) ) :
              print "runSim: Test still running after %d secs" %runtime
              lasttime = runtime

  if timedout == 0:

    # Just let it go until the end...
    timedout = PollforTestEnd(timeout-runtime)
    runtime = int(time.time()) - starttime
    retval = CSim.SimStop(pMetac)
    if retval == 0:
      if verbose == 1:
        print "\nRun on Simulator succesful in %d seconds" %runtime
    else:
      if verbose == 1:
        print "Run on Simulator failed. Return value: %d\n" %retval
  else:
    if verbose == 1:
      print "\n Run on Simulator timed out\n"
    retval = -1

  exit (retval)

# End of runSim.py
