#*****************************************************************************
#
#               file : $RCSfile: preout2.py,v $
#             author : $Author: rst $
#  date last revised : $Date: 2012/01/27 15:29:56 $
#    current version : $Revision: 1.16 $
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
#        description : Meta MiniBench initialisation of out2 script
#
#            defines :
#
#****************************************************************************

import os
import sys
from sys import path
import os.path

import shutil

################################################################
# initOut2(threads, theadsmask, perftest)
#
#           threads:    number of threads to initialise
#           theadsmask: bit mask of active threads
#           perftest:   set to enable extra configuration for performance
#                       testing
# 
################################################################
def initOut2(threads, threadsmask, perftest, verbose):
  fout2 = open('out2.txt', 'w')
  
  # Comments at the start of out2.txt
  writemsg = 'CON -- --------\n'
  fout2.write(writemsg)
  writemsg = 'CON -- out2.txt\n'
  fout2.write(writemsg)
  writemsg = 'CON -- --------\n\n'
  fout2.write(writemsg)

  # Delay - workaround lockup issue
  writemsg = '-- Delay before we start\n'
  fout2.write(writemsg)
  writemsg = 'IDL 10\n\n'
  fout2.write(writemsg)

  # Configure nibble 3 to select the thread number based on the number
  # of threads the test runs on
  writemsg = '-- To run the test on any processor thread:\n'
  fout2.write(writemsg)
  writemsg = '-- Set nibble 3 to select the thread number \n'
  fout2.write(writemsg)
  writemsg = '-- For t0 0x0000\n'
  fout2.write(writemsg)
  writemsg = '-- For t1 0x1000\n'
  fout2.write(writemsg)
  writemsg = '-- For t2 0x2000\n'
  fout2.write(writemsg)
  writemsg = '-- For t3 0x3000\n\n'
  fout2.write(writemsg)

  # Check for debug interface privilege
  writemsg = '-- Check for debug interface privilege\n'
  fout2.write(writemsg)
  writemsg = 'POL :REG_JX:0x04830030 0x00000004 0xFFFFFFFF 0 50 200\n\n'
  fout2.write(writemsg)

  # Check for caller options and emit additional out2 initialisation
  if ( perftest == 1 ) :
    writemsg = '-- Performance testing options enabled:\n'
    fout2.write(writemsg)
    writemsg = '-- Disable the core code random staller\n'
    fout2.write(writemsg)
    writemsg = 'WRW :REG_META_TB:0x00000000 0x01E000FF\n\n'
    fout2.write(writemsg)

  # Check for core specific script and invoke additional out2 initialisation
  if os.path.exists("Core.py") :
    if verbose == 1 :
      print "\npreout2: sourcing core specific out2 initialisation"
    fout2.close()
    import Core
    Core.initOut2()
    fout2 = open('out2.txt', 'a')

  # Check for test specific script and invoke additional out2 initialisation
  if os.path.exists("TestCfg.py") :
    if verbose == 1 :
      print "\npreout2: sourcing test specific out2 initialisation"
    fout2.close()
    import TestCfg
    TestCfg.initOut2()
    fout2 = open('out2.txt', 'a')

  if threads not in [0,1,2,3,4]:
    print 'Unknown number of threads: %d \n' %threads
    os.delete('out2.txt')
    sys.exit(2)

  # Quick & dirty count bits in threadsmask and check against threads
  threadcount = 0
  if ( threadsmask & 1 ) != 0 :
    threadcount+=1
  if ( threadsmask & 2 ) != 0 :
    threadcount+=1
  if ( threadsmask & 4 ) != 0 :
    threadcount+=1
  if ( threadsmask & 8 ) != 0 :
    threadcount+=1
  if threadcount != threads :
    print 'Invalid threadsmask for %d threads: %08x \n' %(threads, threadsmask)
    os.delete('out2.txt')
    sys.exit(2)

  # Clear callee-saved registers

  if threads in [1,2,3,4]:

    writemsg = 'MOV :MEM_REG_META_TB:$5 0x0000\n\n'
    fout2.write(writemsg)

    writemsg = '-- Clear callee-saved registers to prevent unnecessary propagation\n'
    fout2.write(writemsg)
    writemsg = '-- of undefined X values in VHDL sim. Other registers are cleared/initialised\n'
    fout2.write(writemsg)
    writemsg = '-- during startup code\n\n'
    fout2.write(writemsg)

    if ( threadsmask & 1 ) != 0 :

      writemsg = '-- Thread 0 -- Clear D0.5\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000051\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 0 -- Clear D1.5\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000052\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 0 -- Clear D0.6\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000061\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 0 -- Clear D1.6\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000062\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 0 -- Clear D0.7\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000071\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 0 -- Clear D1.7\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000072\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n\n'
      fout2.write(writemsg)

      writemsg = 'MOV :MEM_REG_META_TB:$5 0x00000000\n\n'
      fout2.write(writemsg)

    if ( threadsmask & 2 ) != 0 :

      writemsg = 'MOV :MEM_REG_META_TB:$5 0x1000\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 1 -- Clear D0.5\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000051\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 1 -- Clear D1.5\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000052\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 1 -- Clear D0.6\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000061\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 1 -- Clear D1.6\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000062\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 1 -- Clear D0.7\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000071\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 1 -- Clear D1.7\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000072\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n\n'
      fout2.write(writemsg)

      writemsg = 'MOV :MEM_REG_META_TB:$5 0x00000000\n\n'
      fout2.write(writemsg)

    if ( threadsmask & 4 ) != 0 :

      writemsg = 'MOV :MEM_REG_META_TB:$5 0x2000\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 2 -- Clear D0.5\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000051\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 2 -- Clear D1.5\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000052\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 2 -- Clear D0.6\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000061\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 2 -- Clear D1.6\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000062\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 2 -- Clear D0.7\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000071\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 2 -- Clear D1.7\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000072\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n\n'
      fout2.write(writemsg)

      writemsg = 'MOV :MEM_REG_META_TB:$5 0x00000000\n\n'
      fout2.write(writemsg)

    if ( threadsmask & 8 ) != 0 :

      writemsg = 'MOV :MEM_REG_META_TB:$5 0x3000\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 3 -- Clear D0.5\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000051\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 3 -- Clear D1.5\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000052\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 3 -- Clear D0.6\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000061\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 3 -- Clear D1.6\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000062\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 3 -- Clear D0.7\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000071\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = '-- Thread 3 -- Clear D1.7\n'
      fout2.write(writemsg)
      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF0 0x00000000\n'
      fout2.write(writemsg)
      writemsg = 'OR :MEM_REG_META_TB:$6 :MEM_REG_META_TB:$5 0x00000072\n'
      fout2.write(writemsg)
      writemsg = 'WRW :REG_JX:0x0480FFF8 :MEM_REG_META_TB:$6\n'
      fout2.write(writemsg)
      writemsg = 'POL :REG_JX:0x0480FFF8 0x80000000 0x80000000 0 50 200\n\n'
      fout2.write(writemsg)

      writemsg = 'MOV :MEM_REG_META_TB:$6 0x00000000\n\n'
      fout2.write(writemsg)

      writemsg = 'MOV :MEM_REG_META_TB:$5 0x00000000\n\n'
      fout2.write(writemsg)

  fout2.close()


# End of preout2.py
