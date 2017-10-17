#*****************************************************************************
#
#               file : $RCSfile: runSCSim.py,v $
#             author : $Author: lea $
#  date last revised : $Date: 2012/11/08 12:40:29 $
#    current version : $Revision: 1.5 $
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
  if CSimStatus != 0 :
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

  if verbose == 1 :
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
    if verbose == 1 :
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

############################################################################
# Execute the SysCSim

def executeSCSim(T0A0=None, T0PC=None, T1A0=None, T1PC=None, TXSTATUS=None,
                 TXENABLE=None, threads=None):
    
    print "runSCSim: SystemC Simulation Setup"
    
    if threads > 2:
        print "Not running a multi-threaded test > 2 threads"
        sys.exit(2)
    
    import swig_mod
    
    Meta3Runtime = 4000
    if os.environ.has_key("METAG_META3_RUNTIME"):
        Meta3Runtime = long(os.environ['METAG_META3_RUNTIME'])
    print "\nrunSCSim: meta3 runtime " + str(Meta3Runtime)
    
    meta3 = swig_mod.meta_env_wrap(Meta3Runtime)
    
    # Load the memory image
    print "\nrunSCSim: Loading the memory image"
    retval = meta3.load_memory_image(long('0x30000000',16), long('0x01000000',16), 'Ext-st.bin');
    if retval == swig_mod.MBSIM_FAILED:
        return retval
    
    # Start threads - write TXENABLE
    print "runSCSim: Start threads - write TXENABLE"
    for txe in TXENABLE:
        (addr, data) = txe
        meta3.memory_write(long(addr,16), long(data,16))
    
	############################################################################
	# Write the CSim state to SCSim of T[0|1][A0|PC]
    
    print "\nrunSCSim: Write T[0|1][A0|PC]"
    thread=0
    meta3.write_register(thread, meta3.e_Unit_A0, 0, long(T0A0,16))
    meta3.set_pc(thread, long(T0PC,16))
    
    if threads > 1:
        thread=1
        meta3.write_register(thread, meta3.e_Unit_A0, 0, long(T1A0,16))
        meta3.set_pc(thread, long(T1PC,16))
    
    # Configure TXSTATUS for all threads
    print "\nrunSCSim: Write TXSTATUS"
    for txs in TXSTATUS:
        (addr, data) = txs
        meta3.memory_write(long(addr,16), long(data,16))
    
    # Setup SystemC stop mode to be instant (not at the end of the clock cycle)
    meta3.setStopMode()

    cycle = False
    if os.environ.has_key("METAG_META3_CYCLE"):
        cycle = True
    print "\nrunSCSim: cycle mode " + str(cycle)
    
    print "\nrunSCSim: SystemC Simulation Starts"
    print ""
    
    # Start the simulation
    try:
        if not cycle:
            meta3.start_sim()
        else:
            pValuePC = swig_mod.new_ImgUint32_p ()
            while(True):
                meta3.advance_sim(1)
                thread=0
                valuePC = swig_mod.ImgUint32_p_assign (pValuePC, long('0xBADF00D',16))
                meta3.read_register(thread, meta3.e_Unit_PC, 0, pValuePC)
                valuePC = swig_mod.ImgUint32_p_value (pValuePC)
                print "read_register thread " + str(thread) + " PC " + str(hex(valuePC))
    except Exception, err:
        print type(err)
        print "Error: Exception thrown from SysCSim " + str(err)
        sys.exit(2)
    
    print "\nrunSCSim: SystemC Simulation Ended"
    print ""
    
    ############################################################################
    # Testing register read A1Gbp
    
    print "SystemC Test register read A1Gbp"
    print ""
    
    thread=0
    pValue = swig_mod.new_ImgUint32_p ()
    value = swig_mod.ImgUint32_p_assign (pValue, long('0xBADF00D',16))
    meta3.read_register(thread, meta3.e_Unit_A1, 0, pValue)
    value = swig_mod.ImgUint32_p_value (pValue)
    print "read_register thread " + str(thread) + " A1Gbp " + str(hex(value))
    
    if threads > 1:
        thread=1
        value = swig_mod.ImgUint32_p_assign (pValue, long('0xBADF00D',16))
        meta3.read_register(thread, meta3.e_Unit_A1, 0, pValue)
        value = swig_mod.ImgUint32_p_value (pValue)
        print "read_register thread " + str(thread) + " A1Gbp " + str(hex(value))
    
    print ""
    return 0

###################################################
# Gives the hexadecimal representation of an integer
# toHex <num>
###################################################
def toHex(num) :
  return "%08X" %num

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

  keys = os.environ.keys()
  
  from re import search
  
  for key in keys:
    if not search("METACNAME", key):
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
    print "Running simulator in transaction mode, execution cycles will be %d" %exeCycles
  else :
    print "Running simulator in normal mode, execution cycles will be %d" %exeCycles

  if SyncTiming == 1 :
    exeCycles = 1
    print "Running simulator in event synchronisation mode, file name: %s Cycle:%d" %(SyncFileName, exeCycles)

  if mtx == 1 :
    # MTX trumps all as it needs to work on a single cycle basis to ensure GPIO
	# loopback
    exeCycles = 1

  # Timeout defaults to 60 secs, or override with METAT_ONETEST_TIMEOUT value if def'd
  timeout = int(60)
  for key in keys:
    if search("METAT_ONETEST_TIMEOUT", key):
      timeout = int(os.environ['METAT_ONETEST_TIMEOUT'])
      if verbose == 1 :
        print "runSim: Test timeout set to %d secs" %timeout

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

  import CSim

  # Start the Simulator
  pMetac = CSim.SimStart(opts, args, None)

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

    if verbose == 1 :
      print "\nrunSim: Running thread(s) startup"
    ldrout.StartThreads()

    # Wait until all running threads report that they have reach log start point.
    # Loop exits via 1 of 2 breaks tested within the loop
    while 1 :
      # Cause the CSim to execute a bit...
      ExecuteCheckEvents (pMetac, exeCycles)

      # Now check to see if we have reached start of logging on all threads.
      for thread in range(0, maxthreads) :
        tstates[thread] = CSim.QueryThreadState(pMetac, thread)

      # test that all threads are ready...
      if tstates.count(3) == threads :
        break

      # Test for timeout
      runtime = int(time.time()) - starttime
      if runtime >= timeout :
        timedout = 1
        if verbose == 1 :
          print "\nrunSim: Test initialisation timed out after %d secs" %runtime
        break
      else :
        if ( verbose == 1 ) and ( lasttime != runtime ) :
          print "runSim: Test initialisation still running after %d secs" %runtime
          lasttime = runtime

  if timedout == 0:

    if (verbose == 1 ) :
      if ( forceinsimlog == 0 ):
        print "\nrunSim: Reached start of logging after %d secs" %runtime
      else :
        print "\nrunSim: Starting logs from reset"

    Minibench.DCacheFlush(dcache_size, 0)

    # Setup start state MemDump with library module and thread state(0-start state and 1-end state)
    MemorySetup.MemDump(Minibench, 0)
    
	# Dumps from CSim various registers into out2.txt
    Minibench.RegDump2out2(threads, threadsmask, 0, start_intrusive, out2polls)
    
    ############################################################################
    # Capture state of CSim so that SysCSim can be run after CSim 
    ############################################################################
    
    print "\nrunSCSim: Capturing state of CSim for SysCSim"
    
    if not os.path.exists('Ext-st.bin'):
        print '\nrunSCSim: Memory image file Ext-st.bin does not exist!'
        sys.exit(1)
    
	############################################################################
	# Read from CSim of T[0|1][A0|PC]
    print "\nrunSCSim: Read from CSim of T[0|1][A0|PC]"
    
    thread=0
    T0A0 = toHex( long(Minibench.A0Uspecifier, 16) | long(Minibench.T0specifier, 16) )
    T0A0 = Minibench.ProcessCoreRead(T0A0, 1)
    print "runSCSim: CSim T0A0 " + T0A0
    
    T0PC = toHex( long(Minibench.PCUspecifier, 16) | long(Minibench.T0specifier, 16) )
    T0PC = Minibench.ProcessCoreRead(T0PC, 1)
    print "runSCSim: CSim T0PC " + T0PC
    
    T1A0 = None
    T1PC = None
    if threads > 1:
        thread=1
        T1A0 = toHex( long(Minibench.A0Uspecifier, 16) | long(Minibench.T1specifier, 16) )
        T1A0 = Minibench.ProcessCoreRead(T1A0)
        print "runSCSim: CSim T1A0 " + T1A0
        
        T1PC = toHex( long(Minibench.PCUspecifier, 16) | long(Minibench.T1specifier, 16) )
        T1PC = Minibench.ProcessCoreRead(T1PC)
        print "runSCSim: CSim T1PC " + T1PC
    
    ############################################################################
	# Read from CSim of T[0|1][A0|PC]
    print "\nrunSCSim: Read from CSim TXSTATUS"
    
    TXSTATUS=[]
    meta3_maxthreads = 2
    for thread in range(0, meta3_maxthreads) :
        addr = "0x0480%d010" %thread
        readAddr = int(addr, 16)
        readAddrStr = str(hex(readAddr))
        data = CSim.MemRead(":REGMETA:" +readAddrStr)
        print "runSCSim: CSim Register read addr %s data %s" % (readAddrStr, str (hex(data)) )
        TXSTATUS.append( [readAddrStr, str(hex(data)) ] )
    
    ############################################################################
	# Read from CSim of TXENABLE
    print "\nrunSCSim: Read from CSim TXENABLE"
    
    TXENABLE=[]
    meta3_maxthreads = 2
    for thread in range(0, meta3_maxthreads) :
        addr = "0x0480%d000" %thread
        readAddr = int(addr, 16)
        readAddrStr = str(hex(readAddr))
        data = CSim.MemRead(":REGMETA:" +readAddrStr)
        print "runSCSim: CSim Register read addr %s data %s" % (readAddrStr, str (hex(data)) )
        TXENABLE.append( [readAddrStr, str(hex(data)) ] )
    
    ############################################################################
    # Continue test on CSim

    print "\nrunSCSim: Continue runnning the test on CSim"
    print ""

    if forceinsimlog == 0 :
      # If we're at InSimStartEvt, need to acknowledge
      if verbose == 1 :
        print "\nrunSim: Restarting thread(s)"
      CSim.AckLogEvent(pMetac)
    else:
      # Running from boot, just get it going
      if verbose == 1 :
        print "\nrunSim: Starting thread(s) from reset"
      ldrout.StartThreads()

    if os.path.exists("dbgsim.py") :
      # If the test provided a debug script, run it now..
      if verbose == 1 :
        print "\nrunSim: Running debug script.."

      import dbgsim
      dbgsim.dbgSim(verbose, pMetac)

      if verbose == 1 :
        print "\nrunSim: Debug script completed after %d secs" %(int(time.time()) - starttime)

      # ..and cat the debug out2 into ours
      fout2 = open('out2.txt', 'a')
      shutil.copyfileobj(open('dbgsim_out2.txt','r'), fout2)
      fout2.close()

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

         # test that all threads are ready...
         if tstates.count(4) == threads :
           break

         # Test for timeout
         runtime = int(time.time()) - starttime
         if runtime >= timeout :
           timedout = 1

           if verbose == 1 :
            print "\nrunSim: Test run timed out after %d secs" %runtime

           break
         else :
           if ( (verbose == 1) and (lasttime != runtime) ) :
            print "runSim: Test still running after %d secs" %runtime
            lasttime = runtime

  if timedout == 0:

    if insimlogend == 0 :
      # At test logging end point
      if verbose == 1  :
        print "\nrunSim: Reached end of logging after %d secs" %runtime
      Minibench.RegDump2out2(threads, threadsmask, 1, start_intrusive, out2polls)

      # out2.txt actually needs a poll to ensure the purge is complete. Hence
      # the use of DCachePurge below. Also, will not want all the individual
      # cache line flushes of Minibench.DCacheFlush to appear in the out2.txt so
      # the DCachePurge below is sufficient.
      # Note - is only needed for writeback cache cores, so need to move this out
      # into the relevent core specific script to invoke via Regs2out2end()
      Minibench.DCachePurge()

      # Setup end state MemDump with library module and thread state(0-start state and 1-end state)
      MemorySetup.MemDump(Minibench, 1)
      CSim.AckLogEvent(pMetac)

    # Just let it go until the end...
    timedout = PollforTestEnd(timeout-runtime)

    runtime = int(time.time()) - starttime

    if timedout == 0 :
      if insimlogend == 0 :
        if verbose == 1 :
          print "\nrunSim: Test endpoint reached after %d secs" %runtime
      else:
        if verbose == 1 :
          print "\nrunSim: Test endpoint reached after %d secs; dumping end state" %runtime
        Minibench.RegDump2out2(threads, threadsmask, 1, start_intrusive, out2polls)
        MemorySetup.MemDump(Minibench, 1)

    else :
      if verbose == 1 :
        print "\nrunSim: Poll for Test End timed out after %d secs" %runtime

  # Stop the Simulator
  retval = CSim.SimStop(pMetac)

  if timedout == 0 :

    if verbose == 1 :
      print "\nrunSim: Test completed after %d secs" %runtime
    else :
      print "\n"

    if retval == 0 :
      print "Run on Simulator successful \n"
      
      # Execute on meta3 sim
      retval = executeSCSim(T0A0, T0PC, T1A0, T1PC, TXSTATUS, TXENABLE, threads)
      if retval == 0:
        print "Run on SCSim successful\n"
      else:
        print "Run on SCSim failed. Return value: %d\n" %retval
    else:
      print "Run on Simulator failed. Return value: %d\n" %retval

  else:
    print "\n Run on Simulator timed out\n"
    retval = -1

  exit (retval)

# End of runSim.py
