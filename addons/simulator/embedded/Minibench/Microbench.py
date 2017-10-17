#*****************************************************************************
#
#               file : $RCSfile: Microbench.py,v $
#             author : $Author: rst $
#  date last revised : $Date: 2012/02/17 17:34:10 $
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
#        description : Meta MiniBench Microbench; slimmed down version that just
#                      generates an out2.txt scripts for the VHDL testbench
#
#            defines :
#
#****************************************************************************

import os
import shutil
import sys
import time
import re
from re import *

# The Target on which the test runs
Target = None

# Variable to set Console logging
Progress = None

# Flag whether target is MTX or not.
Mtx = 0

# TXUXXRX addresses
TxrxrqAddr = '0480FFF8'
TxrxdtAddr = '0480FFF0'
TxrxrqReadbit = '00010000'

# Thread Specifier
T0specifier = '00000000'
T1specifier = '00001000'
T2specifier = '00002000'
T3specifier = '00003000'

# TXUXXRXRQ Uspecifier
D0Uspecifier = '00000001'
A0Uspecifier = '00000003'
PCUspecifier = '00000005'

# TXENABLE addresses
T0ENABLE = '04800000'
T1ENABLE = '04801000'
T2ENABLE = '04802000'
T3ENABLE = '04803000'

# TXSTATUS addresses
T0STATUS = '04800010'
T1STATUS = '04801010'
T2STATUS = '04802010'
T3STATUS = '04803010'

# L2 control regs addresses
SYSC_L2C_INIT   = '048300C0'
SYSC_L2C_ENABLE = '048300D0'

# Max no. of segments in a seg mmu core
maxSegs = 12

# Lists to maintain start, length and end addresses for all the segments in a seg mmu core

# Buffer to hold starting physical addresses of segments
baseaddr = [0]*maxSegs

# Buffer to hold each segment's thread and write access bits
segaccess = [0]*maxSegs

# Buffers to hold starting output address 0:31(lower address bits) and 32:63(upper address bits)
start32 = [0]*maxSegs
start64 = [0]*maxSegs

# Buffers to hold end output address 0:31(lower address bits) and 32:63(upper address bits)
end32 = [0]*maxSegs
end64 = [0]*maxSegs

# Buffer to hold the length of each segment
segLen = [0]*maxSegs

# Bits that configure the testbench register for all the used segments
SegConfigBits = '0x00000000'

# TestBench register start address for windows
WinStart = '0x2010'

# Segment Base Address registers base address
segBase = '0x04850000'

# Segment Limit registers base address
segLimit = '0x04850004'

# Segment Output Address 0 registers base address
segOutA0 = '0x04850008'

# Segment Output Address 1 registers base address
segOutA1 = '0x0485000C'

# Enhanced bypass/wr combiner control registers base address
ebwcCrtl = '0x04830640'

# Pointers to physical memory available in simulator
# If physMemPtr==0, use new memory allocator API
physMemPtr = '0'
physMemRem = '0'
# Default memory to get from allocator
#physMemDefaultBase = '0xB0000000'
#physMemDefaultLen  = '0x01000000'

###################################################
# Address mappings for PM Dump
###################################################

# Cache Partitioning Masks
Sys_Dc0 = ":REGMETA:04830200"
Sys_Dc1 = ":REGMETA:04830208"
Sys_Dc2 = ":REGMETA:04830210"
Sys_Dc3 = ":REGMETA:04830218"
Sys_Ic0 = ":REGMETA:04830220"
Sys_Ic1 = ":REGMETA:04830228"
Sys_Ic2 = ":REGMETA:04830230"
Sys_Ic3 = ":REGMETA:04830238"

# Cache/MMU bypass control
Sys_CM_Config = ":REGMETA:04830028"

# MMU RAM Cache Validate
LinSysCflush_Mmcu = ":REGMETA:04700000"

# MMU Base Address
Mmcu_Table_Phys = ":REGMETA:04830010"

# Data/Code Cache Enable/Flush
DcEnable = ":REGMETA:04830018"
IcEnable = ":REGMETA:04830020"
DcFlush = ":REGMETA:04830038"
IcFlush = ":REGMETA:04830040"

###################################################
# JTAG control registers and bits
###################################################
MDbgCtrl1Addr      = "0x0000000C"
DbgCtrl1_Intrusive = "0x00000040"
DbgCtrl1_Lock2     = "0x00010000"
DbgCtrl1_Lock2Lock = "0x20000000"


###################################################
# Print comment
# COM <Comment>
###################################################
def Com(strLine) :

  Target.Com(strLine)

  return


###############################################################################
#
# RunThreads(threads, threadsmask, start_intrusive, out2polls)
#
# Generate out2 script to start threads running, poll for threads halted and
# check end state
# Uses Mtx global flag
# Writes to postOut2.txt
#
# threads     
# threadsmask 
# start_intrusive 0(don't)/1(do)
# out2polls
#
###############################################################################

def RunThreads(threads, threadsmask, start_intrusive, out2polls) :

  # Check for core specific script and invoke additional out2 registers setup before we start the threads running
  # Omitting this for now (Core.py files would need updating for alternate out2 output file)
  #if os.path.exists("Core.py") :
  #  import Core
  #  Core.Regs2out2start()

  # Check for test specific script and invoke additional out2 registers setup before we start the threads running
  # Omitting this for now (TestCfg.py files would need updating for alternate out2 output file)
  #if os.path.exists("TestCfg.py") :
  #  import TestCfg
  #  TestCfg.Regs2out2start()

  # Start Threads
  Writetxt2out2('postOut2.txt', '\n-- Start Threads')

  # First set lock2 (and intrusive if need)
  MDbgCtrl1Val = long(DbgCtrl1_Lock2, 16)

  if start_intrusive == 1 :
    MDbgCtrl1Val |= long(DbgCtrl1_Intrusive, 16)

  txt = 'WRW :REG_JD:' + MDbgCtrl1Addr + ' 0x' + toHex(MDbgCtrl1Val)
  Writetxt2out2('postOut2.txt', txt)
  txt = 'POL :REG_JD:' + MDbgCtrl1Addr + ' ' + DbgCtrl1_Lock2Lock + ' ' + DbgCtrl1_Lock2Lock + ' 0 50 200'
  Writetxt2out2('postOut2.txt', txt)

  if ( threadsmask & 1 ) != 0 :
    ProcessStThd(T0ENABLE)

  if ( threadsmask & 2 ) != 0 :
    ProcessStThd(T1ENABLE)

  if ( threadsmask & 4 ) != 0 :
    ProcessStThd(T2ENABLE)

  if ( threadsmask & 8 ) != 0 :
    ProcessStThd(T3ENABLE)

  # Now clear lock2
  MDbgCtrl1Val = 0
  if start_intrusive == 1 :
    MDbgCtrl1Val |= long(DbgCtrl1_Intrusive, 16)
  txt = 'WRW :REG_JD:'+ MDbgCtrl1Addr + ' 0x' + toHex(MDbgCtrl1Val)
  Writetxt2out2('postOut2.txt', txt)

  # Poll for test end
  txt = '\n-- Poll for Test End (allows ' + str(out2polls * 20000) + ' cycles)'
  Writetxt2out2('postOut2.txt', txt)
  if ( threadsmask & 1 ) != 0 :
    txt = 'POL :REG_JX:0x' + T0ENABLE + ' 0x00000000 0x00000001 0 ' + str(out2polls) + ' 20000'
    Writetxt2out2('postOut2.txt', txt)
  if ( threadsmask & 2 ) != 0 :
    txt = 'POL :REG_JX:0x' + T1ENABLE + ' 0x00000000 0x00000001 0 ' + str(out2polls) + ' 20000'
    Writetxt2out2('postOut2.txt', txt)
  if ( threadsmask & 4 ) != 0 :
    txt = 'POL :REG_JX:0x' + T2ENABLE + ' 0x00000000 0x00000001 0 ' + str(out2polls) + ' 20000'
    Writetxt2out2('postOut2.txt', txt)
  if ( threadsmask & 8 ) != 0 :
    txt = 'POL :REG_JX:0x' + T3ENABLE + ' 0x00000000 0x00000001 0 ' + str(out2polls) + ' 20000'
    Writetxt2out2('postOut2.txt', txt)

  # Check for core specific script and emit additional out2 setup before we poll the threads
  # Omitting this for now (Core.py files would need updating for alternate out2 output file)
  #if os.path.exists("Core.py") :
  #  import Core
  #  Core.Regs2out2end()

  # Check for test specific script and emit additional out2 setup before we poll the threads
  # Omitting this for now (TestCfg.py files would need updating for alternate out2 output file)
  #if os.path.exists("TestCfg.py") :
  #  import TestCfg
  #  TestCfg.Regs2out2end()

  # Make sure no threads crashed - poll threads TXSTATUS: FReason and HReason 
  Writetxt2out2('postOut2.txt', '\n-- Poll TXSTATUS: FReason and HReason for all threads') 
  if ( threadsmask & 1 ) != 0 :
    # Check the thread 0 FReason and HReason flags
    Writetxt2out2('postOut2.txt', '-- Poll Thread 0 TXSTATUS: FReason and HReason')
    txt = 'POL :REG_JX:0x' + T0STATUS + ' 0x00000000 0x003C0000 0 50 200'
    Writetxt2out2('postOut2.txt', txt)

  if ( threadsmask & 2 ) != 0 :
    # Check the thread 1 FReason and HReason flags
    Writetxt2out2('postOut2.txt', '-- Poll Thread 1 TXSTATUS: FReason and HReason')
    txt = 'POL :REG_JX:0x' + T1STATUS + ' 0x00000000 0x003C0000 0 50 200'
    Writetxt2out2('postOut2.txt', txt)

  if ( threadsmask & 4 ) != 0 :
    # Check the thread 2 FReason and HReason flags
    Writetxt2out2('postOut2.txt', '-- Poll Thread 2 TXSTATUS: FReason and HReason')
    txt = 'POL :REG_JX:0x' + T2STATUS + ' 0x00000000 0x003C0000 0 50 200'
    Writetxt2out2('postOut2.txt', txt)

  if ( threadsmask & 8 ) != 0 :
    # Check the thread 3 FReason and HReason flags
    Writetxt2out2('postOut2.txt', '-- Poll Thread 3 TXSTATUS: FReason and HReason')
    txt = 'POL :REG_JX:0x' + T3STATUS + ' 0x00000000 0x003C0000 0 50 200'
    Writetxt2out2('postOut2.txt', txt)

  # Check threads return values
  Writetxt2out2('postOut2.txt', '\n-- Poll return value for all threads') 
  if ( threadsmask & 1 ) != 0 :
    # Check the thread 0 return value
    Writetxt2out2('postOut2.txt', '-- Poll Thread 0 D0Re0 return value')
    T0D0 = toHex( long(D0Uspecifier, 16) | long(T0specifier, 16) )
    txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + toHex( long(T0D0, 16) | long(TxrxrqReadbit, 16) )
    Writetxt2out2('postOut2.txt', txt)
    txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
    Writetxt2out2('postOut2.txt', txt)
    txt = 'POL :REG_JX:0x' + TxrxdtAddr + ' 0x00000000 0xFFFFFFFF 0 50 200'
    Writetxt2out2('postOut2.txt', txt)

  if ( threadsmask & 2 ) != 0 :
    # Check the thread 1 return value
    Writetxt2out2('postOut2.txt', '-- Poll Thread 1 D0Re0 return value')
    T1D0 = toHex( long(D0Uspecifier, 16) | long(T1specifier, 16) )
    txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + toHex( long(T1D0, 16) | long(TxrxrqReadbit, 16) )
    Writetxt2out2('postOut2.txt', txt)
    txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
    Writetxt2out2('postOut2.txt', txt)
    txt = 'POL :REG_JX:0x' + TxrxdtAddr + ' 0x00000000 0xFFFFFFFF 0 50 200'
    Writetxt2out2('postOut2.txt', txt)

  if ( threadsmask & 4) != 0 :
    # Check the thread 2 return value
    Writetxt2out2('postOut2.txt', '-- Poll Thread 2 D0Re0 return value')
    T2D0 = toHex( long(D0Uspecifier, 16) | long(T2specifier, 16) )
    txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + toHex( long(T2D0, 16) | long(TxrxrqReadbit, 16) )
    Writetxt2out2('postOut2.txt', txt)
    txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
    Writetxt2out2('postOut2.txt', txt)
    txt = 'POL :REG_JX:0x' + TxrxdtAddr + ' 0x00000000 0xFFFFFFFF 0 50 200'
    Writetxt2out2('postOut2.txt', txt)

  if ( threadsmask & 8 ) != 0 :
    # Check the thread 3 return value
    Writetxt2out2('postOut2.txt', '-- Poll Thread 3 D0Re0 return value')
    T1D0 = toHex( long(D0Uspecifier, 16) | long(T3specifier, 16) )
    txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + toHex( long(T3D0, 16) | long(TxrxrqReadbit, 16) )
    Writetxt2out2('postOut2.txt', txt)
    txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
    Writetxt2out2('postOut2.txt', txt)
    txt = 'POL :REG_JX:0x' + TxrxdtAddr + ' 0x00000000 0xFFFFFFFF 0 50 200'
    Writetxt2out2('postOut2.txt', txt)

  return


###################################################
# Gives the hexadecimal representation of an integer
# toHex <num>
###################################################
def toHex(num) :
  return "%08X" %num


###################################################
# Write text in out2.txt
# Writetxt2out2 <filename> <line>
###################################################
def Writetxt2out2(file, line) :
  fout2 = open(file, 'a')
  str = line + '\n'
  fout2.write(str)
  fout2.close()
  return


###################################################
# Write Start threads command to postOut2.txt
# ProcessStThd <TXENABLE>
###################################################
def ProcessStThd(txenable) :
  strline = txenable
  #str = strline.split()[1:]

  fout2 = open('postOut2.txt', 'a')
  txt = 'WRW :REG_JX:0x' + txenable + ' 0x00000001\n'
  fout2.write(txt)
  fout2.close()
  return


###############################################################################
#
# Out2MemSetup(memtype, strtaddr, addrlen, thrdst)
#
# Set memory base addresses, and malloc in out2.txt
#
# memtype (0-ext/1-corecode/2-coredata)
# strtaddr
# addrlen
#
###############################################################################

def Out2MemSetup( memtype, strtaddr, addrlen ) :

  # Memory type - External memory
  if memtype == 0 :
    if Progress == 1 :
      print "\nSetting up external memory"
    Writetxt2out2('out2.txt', '\n-- Base address for external memory')
    txt = 'MOV :MEM_META_MAIN:$1 ' + strtaddr + '\n'
    Writetxt2out2('out2.txt', txt)
    Writetxt2out2('out2.txt', '-- Set external memory start address')
    Writetxt2out2('out2.txt', 'WRW :REG_META_TB:0x00000250 :MEM_META_MAIN:$1\n')
    txt = 'MALLOC :MEM_META_MAIN:EXT0 ' + addrlen + ' 0x00800000'
    Writetxt2out2('out2.txt', txt)
    txt = 'LDB :MEM_META_MAIN:EXT0:0x0 ' + addrlen + ' 0x00000000 Ext.bin\n'
    Writetxt2out2('out2.txt', txt)

  # Memory type - CoreCode memory
  if memtype == 1 :
    if Progress == 1 :
      print "\nSetting up CoreCode memory"
    txt = '\nMALLOC :MEM_META_CCM:CORECODE ' + addrlen + ' 0x4'
    Writetxt2out2('out2.txt', txt)
    txt = 'LDB :MEM_META_CCM:CORECODE:0x0 ' + addrlen + ' 0x00000000 CoreCode.bin\n'
    Writetxt2out2('out2.txt', txt)

  # Memory type - CoreData memory
  if memtype == 2 :
    if Progress == 1 :
      print "\nSetting up CoreData memory"
    txt = '\nMALLOC :MEM_META_CDM:COREDATA ' + addrlen + ' 0x4'
    Writetxt2out2('out2.txt', txt)
    txt = 'LDB :MEM_META_CDM:COREDATA:0x0 ' + addrlen + ' 0x00000000 CoreData.bin\n'
    Writetxt2out2('out2.txt', txt)

  if Progress == 1 :
    print ""

  return


###############################################################################
#
# Out2MtxCoreMemSetup(memtype, strtaddr, addrlen, thrdst)
#
# Set memory base addresses, and malloc in out2.txt
#
# memtype (1-corecode)
# strtaddr
# addrlen
#
# MTX organises core memories as adjacent blocks of 32KB
#
###############################################################################

def Out2MtxCoreMemSetup(memtype, strtaddr, addrlen ) :

  if Progress == 1 :
    txt = '\nSetting up MTX memory type %d at ' %memtype + strtaddr + ' for ' + addrlen + ' bytes'
    print txt

  # Memory type - CoreCode memory
  if memtype == 1 :
    txt = '\n-- Allocate core code memories'
    Writetxt2out2('out2.txt', txt)
    memsize = long('0x00008000', 16)
    curofs = 0
    while ( curofs < long(addrlen, 16) ) :
      memno = str( curofs / memsize )
      if Progress == 1 :
        txt = '   Core Code memory ' + memno + ' at offset 0x%08X bytes' %curofs
        print txt
      txt = 'MALLOC :MEM_MTX_CM_' + memno +':CORECODE 0x' + toHex(memsize) + ' 0x4'
      Writetxt2out2('out2.txt', txt)
      filename = 'CoreCode_' + memno + '.bin'
      txt = 'LDB :MEM_MTX_CM_' + memno +':CORECODE:0x0 0x' + toHex(memsize) + ' 0x00000000 ' + filename
      Writetxt2out2('out2.txt', txt)
      curofs += memsize
    if Progress == 1 :
      print "   ..done"

  else:
    print "Minibench: Error: MTX core memory invalid memory type"

  if Progress == 1 :
    print ""

  return

###################################################
# Sets up default external memory: 32MB at 0xB0000000
# ExtMemDeclare
###################################################
def ExtMemDeclare() :
  # Just a dummy, as CSim is not involved here
  return


###################################################
# Sets up default external memories: 32MB at 0xB0000000
# SegMMU case, with alias at 0x30000000
# ExtMemDeclareM
###################################################
def ExtMemDeclareM() :
  global physMemPtr
  global physMemRem

  if Progress == 1:
    print "Minibench: acquiring default memory.."

  result =Target.PhysMemDeclare ('0xFFFFFFFF70000000', '0x0000000030000000', \
    '0x0000000002000000', '64', 'SDRAM')
  if result == 0:
    physMemPtr = '0xB0000000'
    physMemRem = '0x02000000'
    if Progress == 1:
      print "\t..OK"
  else :
    if Progress == 1:
      print "\t..failed; returned 0x%08x" %(result)

  return


###################################################
# Declare a SegMMU segment to the testbench
# SegMMUSegDecl <SegmentID> <startaddress> <addresslength>
###################################################
def SegMMUSegDecl(segID, strtaddr, addrlen) :
  global baseaddr
  global segaccess
  global start32
  global start64
  global end32
  global end64
  global segLen
  global SegConfigBits
  global physMemPtr
  global physMemRem

  if Progress == 1:
    txt = 'Minibench: test uses segment ' + str(segID) + ': base 0x' + \
      toHex(long(strtaddr, 16)) + '; length 0x' + toHex(long(addrlen, 16)) + ';'
    print txt

  # Collect the start and end addresses of the segments
  for i in range (0, maxSegs) :
    if segID == i :

      baseaddr[i] = strtaddr
      segLen[i] = addrlen

      # Segment access allows all threads read/write access
      segaccess[i] = (long('0xF02', 16))

      # Set output address
      start32[i] = '0x' + toHex(long(physMemPtr,16) & long('0xFFFFFFFF', 16))
      start64[i] = '0x' + toHex(long(physMemPtr,16) >> 32)

      # Work out how much is left
      physMemPtr = '0x' + toHex(long(physMemPtr,16) + long(addrlen, 16))
      physMemRem = '0x' + toHex(long(physMemRem,16) - long(addrlen, 16))

      if Progress == 1:
        txt = '           mapped to: 0x' + toHex(long(start32[i], 16)) + ', ' + toHex(long(physMemRem, 16)) + ' remaining.'
        print txt

      SegConfigBits = '0x' + toHex(long(SegConfigBits,16) | (long('0x1', 16) << segID) )

  return


###################################################
# Sets up the segments in a SegMMU core
# SegMMUMemSetup
###################################################
def SegMMUMemSetup() :
  global baseaddr
  global segaccess
  global start32
  global start64
  global end32
  global end64
  global segLen
  global SegConfigBits

  # Program the testbench active registers
  Writetxt2out2('out2.txt', '\n-- Enable active windows')
  txt = 'WRW :REG_META_TB:0x00002000 ' + SegConfigBits
  Writetxt2out2('out2.txt', txt)

  if Progress == 1:
    txt = 'Minibench: enable active windows in the testbench: 0x' + toHex(long(SegConfigBits, 16)) + '.'
    print txt

  for i in range (0, maxSegs) :

    # Check if the segment is configured
    if segLen[i] != 0 :

      #
      # Set the segment base & limit registers for this segment,
      # We also need to set the correct output address mapping as well.
      # after set BASE,LIMIT,OUTA0 registers, we need to write to OUTA1 register to make 
      # it take effect.
      #
      if Progress == 1:
        txt = 'Minibench: enabling segment ' + str(i) + ': base 0x' + toHex(long(baseaddr[i], 16)) + '; length 0x' + toHex(long(segLen[i], 16)) + ';'
        print txt
        txt = '           mapped to: 0x' + toHex(long(start64[i], 16)) + '_' + toHex(long(start32[i], 16)) + ';'
        print txt

      txt = '\n-- Set the segment base & limit registers for segment ' + str(i)
      Writetxt2out2('out2.txt', txt)

      segBaseAdr = '0x' + toHex(long(segBase, 16) + i*long('10', 16))
      segBaseVal = '0x' + toHex( (long(baseaddr[i], 16) & long('0xFFFFFFFF', 16) ) | segaccess[i] )
      txt = 'WRW :REG_JX:' + segBaseAdr + ' ' + segBaseVal
      Writetxt2out2('out2.txt', txt)
      # Write to the register in the simulator
      if Progress == 1:
        txt = '           writing base register:  0x' + toHex(long(segBaseAdr, 16)) + ', 0x' + toHex(long(segBaseVal, 16)) + ';'
        print txt
      Target.MemWrite(":REGMETA:" + segBaseAdr, segBaseVal);	

      segLimitAdr = '0x' + toHex(long(segLimit, 16) + i*long('10', 16))
      txt = 'WRW :REG_JX:' + segLimitAdr + ' 0x' + toHex(long(segLen[i],16)-1)
      Writetxt2out2('out2.txt', txt)
      # Write to the register in the simulator
      if Progress == 1:
        txt = '           writing limit register: 0x' + toHex(long(segLimitAdr, 16)) + ', 0x' + toHex(long(segLen[i],16)-1) + ';'
        print txt
      Target.MemWrite(":REGMETA:" + segLimitAdr, toHex(long(segLen[i],16)-1));	

      # Since the base register is changed, the output address is supposed to be changed as well
      # currently we are doing 1 to 1 mapping
      # The value of this outA0 register should be the same as the base register except that
      # bottom 12 bits should be 0
      segOutA0Adr = '0x' + toHex(long(segOutA0, 16) + i*long('10', 16))
      segOutA0Val = '0x' + toHex( (long(start32[i], 16) & long('0xFFFFF000', 16) ) )
      # Write to the register in the simulator
      if Progress == 1:
        txt = '           writing output low:     0x' + toHex(long(segOutA0Adr, 16)) + ', 0x' + toHex(long(segOutA0Val, 16)) + ';'
        print txt
      Target.MemWrite(":REGMETA:" + segOutA0Adr, segOutA0Val);	

      segOutA1Adr = '0x' + toHex(long(segOutA1, 16) + i*long('10', 16))
      segOutA1Val = '0x' + toHex(long(start64[i], 16))
      # Write to the register in the simulator
      if Progress == 1:
        txt = '           writing output high:    0x' + toHex(long(segOutA1Adr, 16)) + ', 0x' + toHex(long(segOutA1Val, 16)) + '.'
        print txt
      Target.MemWrite(":REGMETA:" + segOutA1Adr, segOutA1Val);	

      #
      # Output out2 sequence to allocate physical memory corresponding to the configured segment
      #
      txt = '\n-- Allocate memory to segment ' + str(i)
      Writetxt2out2('out2.txt', txt)
      if i < 10 :
        winnum = '0' + str(i)
      else :
        winnum = str(i)

      txt = 'MALLOC :MEM_META_WIN' + winnum + ':Seg' + winnum +'Adr ' + segLen[i] + ' 0x00001000'
      Writetxt2out2('out2.txt', txt)

      # Set the output address registers for this segment
      txt = '\n-- Set the output address registers for segment ' + str(i)
      Writetxt2out2('out2.txt', txt)
      txt = 'WRW :MEM_META_WIN' + winnum + ':$1 :MEM_META_WIN' + winnum + ':Seg' + winnum + 'Adr:0x0'
      Writetxt2out2('out2.txt', txt)
      txt = 'AND :MEM_META_WIN' + winnum + ':$2 :MEM_META_WIN' + winnum + ':$1 0xFFFFFFFF'
      Writetxt2out2('out2.txt', txt)
      txt = 'SHR :MEM_META_WIN' + winnum + ':$3 :MEM_META_WIN' + winnum + ':$1 32'
      Writetxt2out2('out2.txt', txt)
      txt = 'WRW :REG_JX:0x' + toHex(long(segOutA0, 16) + i*long('10', 16)) + ' :MEM_META_WIN' + winnum + ':$2'
      Writetxt2out2('out2.txt', txt)
      txt = 'WRW :REG_JX:0x' + toHex(long(segOutA1, 16) + i*long('10', 16)) + ' :MEM_META_WIN' + winnum + ':$3'
      Writetxt2out2('out2.txt', txt)

      #
      # Program test bench registers for this window
      # Code here also needs to read back the TB addresses for the segment and set [start|end][32|64]
      #
      winaddr = WinStart
      txt = '\n-- Program test bench registers for WIN' + str(i)
      Writetxt2out2('out2.txt', txt)
      # Setup the WIN register based on the segment MMU register settings
      txt = 'ADD :MEM_META_WIN' + winnum + ':$4 :MEM_META_WIN' + winnum + ':$1 0x' + toHex(long(segLen[i],16)-1) 
      Writetxt2out2('out2.txt', txt)
      # Setup the WIN register based on the segment MMU register settings
      txt = 'AND :MEM_META_WIN' + winnum + ':$5 :MEM_META_WIN' + winnum + ':$4 0xFFFFFFFF'
      Writetxt2out2('out2.txt', txt)
      txt = 'SHR :MEM_META_WIN' + winnum + ':$6 :MEM_META_WIN' + winnum + ':$4 32'
      Writetxt2out2('out2.txt', txt)
      winaddr = '0x' + toHex(long(winaddr, 16) + i*long('40', 16))
      # Value we need to read from the csim and put in start32[i]
      txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$2'
      Writetxt2out2('out2.txt', txt)
      winaddr = '0x' + toHex(long(winaddr, 16) + long('10', 16))
      # Value we need to read from the csim and put in start64[i]
      txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$3'
      Writetxt2out2('out2.txt', txt)
      winaddr = '0x' + toHex(long(winaddr, 16) + long('10', 16))
      # Value we need to read from the csim and put in end32[i]
      txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$5'
      Writetxt2out2('out2.txt', txt)
      winaddr = '0x' + toHex(long(winaddr, 16) + long('10', 16))
      # Value we need to read from the csim and put in end64[i]
      txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$6'
      Writetxt2out2('out2.txt', txt)

  # Flush writes to ensure segmmu & testbench setup complete
  txt = '\n-- Flush writes to ensure segmmu & testbench setup complete'
  Writetxt2out2('out2.txt', txt)
  txt = 'RDW :REG_JX:0x04800000'
  Writetxt2out2('out2.txt', txt)
  txt = 'RDW :REG_META_TB:0x00000000'
  Writetxt2out2('out2.txt', txt)

  txt = ''
  Writetxt2out2('out2.txt', txt)

  return


###################################################
# Sets up a SegMMU core for testing the segmmu
# SegMMUTestSetup
###################################################
def SegMMUTestSetup() :
  global baseaddr
  global segaccess
  global start32
  global start64
  global end32
  global end64
  global segLen
  global SegConfigBits
  global physMemPtr
  global physMemRem

  # Window 11 mallocs from a fixed 0xB0000000 in Pdump
  winID = 11

  # Csim uses default 0xB0000000, 16MB from segment 5
  segID = 5

  if Progress == 1:
    txt = 'Minibench: segmmu test uses segment ' + str(segID) + ';'
    print txt

  # Allocate 16MB to the segment
  baseaddr[winID] = physMemPtr
  segLen[winID] = '0x01000000'

  # Segment access allows all threads read/write access
  segaccess[winID] = (long('0xF02', 16))

  # Set output address
  start32[winID] = '0x' + toHex(long(physMemPtr,16) & long('0xFFFFFFFF', 16))
  start64[winID] = '0x' + toHex(long(physMemPtr,16) >> 32)

  if Progress == 1:
    txt = '           points to: 0x' + toHex(long(start32[winID], 16)) + ' for 0x' + toHex(long(segLen[winID],16)) + ' bytes.'
    print txt

  # Work out how much is left
  physMemPtr = '0x' + toHex(long(physMemPtr,16) + long("0x01000000", 16))
  physMemRem = '0x' + toHex(long(physMemRem,16) - long("0x01000000", 16))

  # Program the testbench active registers - window 5
  SegConfigBits = '0x' + toHex(long(SegConfigBits,16) | (long('0x1', 16) << segID) )
  if Progress == 1:
    txt = 'Minibench: enable active windows in the testbench: 0x' + toHex(long(SegConfigBits, 16)) + '.'
    print txt

  Writetxt2out2('out2.txt', '\n-- Enable active windows')
  txt = 'WRW :REG_META_TB:0x00002000 ' + SegConfigBits
  Writetxt2out2('out2.txt', txt)

  #
  # Set the segment base & limit registers
  # We also need to set the correct output address mapping as well.
  # after set BASE,LIMIT,OUTA0 registers, we need to write to OUTA1 register to make 
  # it take effect.
  #
  if Progress == 1:
    txt = 'Minibench: enabling segment ' + str(segID) + ': base 0x' + toHex(long(baseaddr[winID], 16)) + '; length 0x' + toHex(long(segLen[winID],16)) + ';'
    print txt
    txt = '           mapped to: 0x' + toHex(long(start64[winID], 16)) + '_' + toHex(long(start32[winID], 16)) + ';'
    print txt

  txt = '\n-- Set the segment base & limit registers for segment ' + str(segID)
  Writetxt2out2('out2.txt', txt)

  segBaseAdr = '0x' + toHex(long(segBase, 16) + segID*long('10', 16))
  segBaseVal = '0x' + toHex( (long(baseaddr[winID], 16) & long('0xFFFFFFFF', 16) ) | segaccess[winID] )
  txt = 'WRW :REG_JX:' + segBaseAdr + ' ' + segBaseVal
  Writetxt2out2('out2.txt', txt)
  # Need to write to the register in simulator
  if Progress == 1:
    txt = '           writing base register:  0x' + toHex(long(segBaseAdr, 16)) + ', 0x' + toHex(long(segBaseVal, 16)) + ';'
    print txt
  Target.MemWrite(":REGMETA:" + segBaseAdr, segBaseVal);	

  segLimitAdr = '0x' + toHex(long(segLimit, 16) + segID*long('10', 16))
  txt = 'WRW :REG_JX:' + segLimitAdr + ' 0x' + toHex(long(segLen[winID],16)-1)
  Writetxt2out2('out2.txt', txt)
  # Need to write to the register in simulator
  if Progress == 1:
    txt = '           writing limit register: 0x' + toHex(long(segLimitAdr, 16)) + ', 0x' + toHex(long(segLen[winID],16)-1) + ';'
    print txt
  Target.MemWrite(":REGMETA:" + segLimitAdr, toHex(long(segLen[winID],16)-1));	

  # Since the base register is changed, the output address is supposed to be changed as well
  # currently we are doing 1 to 1 mapping
  # The value of this outA0 register should be the same as the base register except that
  # bottom 12 bits should be 0
  segOutA0Adr = '0x' + toHex(long(segOutA0, 16) + segID*long('10', 16))
  segOutA0Val = '0x' + toHex( (long(start32[winID], 16) & long('0xFFFFF000', 16) ) )
  if Progress == 1:
    txt = '           writing output low:     0x' + toHex(long(segOutA0Adr, 16)) + ', 0x' + toHex(long(segOutA0Val, 16)) + ';'
    print txt
  Target.MemWrite(":REGMETA:" + segOutA0Adr, segOutA0Val);	

  segOutA1Adr = '0x' + toHex(long(segOutA1, 16) + segID*long('10', 16))
  segOutA1Val = '0x' + toHex(long(start64[winID], 16))
  if Progress == 1:
    txt = '           writing output high:    0x' + toHex(long(segOutA1Adr, 16)) + ', 0x' + toHex(long(segOutA1Val, 16)) + '.'
    print txt
  Target.MemWrite(":REGMETA:" + segOutA1Adr, segOutA1Val);	

  #
  # Allocate physical memory corresponding to the configured segment
  #
  segnum = str(segID)
  winnum = str(winID)
  txt = '\n-- Malloc from window ' + winnum + '; should provide 16MB at 0xB0000000'
  Writetxt2out2('out2.txt', txt)

  # Window 11 should give us 0xB0000000, 16MB
  txt = 'MALLOC :MEM_META_WIN' + winnum + ':Seg' + winnum +'Adr ' + segLen[winID] + ' 0x00001000'
  Writetxt2out2('out2.txt', txt)

  # Check Window 11 gave us what we expect
  txt = '\n-- Check the address in window ' + winnum + ' is what we expect (read via TXCATCH1).'
  Writetxt2out2('out2.txt', txt)
  txt = 'WRW :REG_JX:0x04800088 :MEM_META_WIN' + winnum + ':Seg' + winnum + 'Adr:0x0'
  Writetxt2out2('out2.txt', txt)
  txt = 'POL :REG_JX:0x04800088 ' + str(baseaddr[winID]) + ' 0xFFFFFFFF 0'
  Writetxt2out2('out2.txt', txt)

  # Set the output address registers for segment 5
  txt = '\n-- Set the output address registers for segment ' + segnum
  Writetxt2out2('out2.txt', txt)
  txt = 'WRW :MEM_META_WIN' + winnum + ':$1 :MEM_META_WIN' + winnum + ':Seg' + winnum + 'Adr:0x0'
  Writetxt2out2('out2.txt', txt)
  txt = 'AND :MEM_META_WIN' + winnum + ':$2 :MEM_META_WIN' + winnum + ':$1 0xFFFFFFFF'
  Writetxt2out2('out2.txt', txt)
  txt = 'SHR :MEM_META_WIN' + winnum + ':$3 :MEM_META_WIN' + winnum + ':$1 32'
  Writetxt2out2('out2.txt', txt)
  txt = 'WRW :REG_JX:0x' + toHex(long(segOutA0, 16) + segID*long('10', 16)) + ' :MEM_META_WIN' + winnum + ':$2'
  Writetxt2out2('out2.txt', txt)
  txt = 'WRW :REG_JX:0x' + toHex(long(segOutA1, 16) + segID*long('10', 16)) + ' :MEM_META_WIN' + winnum + ':$3'
  Writetxt2out2('out2.txt', txt)

  #
  # Program test bench registers for this window
  # Code here also needs to read back the TB addresses for the segment and set [start|end][32|64]
  #
  winaddr = WinStart
  txt = '\n-- Program test bench registers for Window ' + segnum
  Writetxt2out2('out2.txt', txt)
  # Setup the WIN register based on the segment MMU register settings
  txt = 'ADD :MEM_META_WIN' + winnum + ':$4 :MEM_META_WIN' + winnum + ':$1 0x00FFFFFF'
  Writetxt2out2('out2.txt', txt)
  # Setup the WIN register based on the segment MMU register settings
  txt = 'AND :MEM_META_WIN' + winnum + ':$5 :MEM_META_WIN' + winnum + ':$4 0xFFFFFFFF'
  Writetxt2out2('out2.txt', txt)
  txt = 'SHR :MEM_META_WIN' + winnum + ':$6 :MEM_META_WIN' + winnum + ':$4 32'
  Writetxt2out2('out2.txt', txt)
  winaddr = '0x' + toHex(long(winaddr, 16) + segID*long('40', 16))
  # Value we need to read from the csim and put in start32[i]
  txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$2'
  Writetxt2out2('out2.txt', txt)
  winaddr = '0x' + toHex(long(winaddr, 16) + long('10', 16))
  # Value we need to read from the csim and put in start64[i]
  txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$3'
  Writetxt2out2('out2.txt', txt)
  winaddr = '0x' + toHex(long(winaddr, 16) + long('10', 16))
  # Value we need to read from the csim and put in end32[i]
  txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$5'
  Writetxt2out2('out2.txt', txt)
  winaddr = '0x' + toHex(long(winaddr, 16) + long('10', 16))
  # Value we need to read from the csim and put in end64[i]
  txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$6'
  Writetxt2out2('out2.txt', txt)

  txt = ''
  Writetxt2out2('out2.txt', txt)

  return


###################################################
# Sets up the testbench to allow register access and print strings
# EnablePrinting
# TODO uses fixed location, should be extended to use argument
###################################################
def SegEnablePrinting() :

  Writetxt2out2('out2.txt', '\n-- Enable active windows')
  Writetxt2out2('out2.txt', 'RDW :MEM_REG_META_TB:$10 :REG_META_TB:0x00002000')
  Writetxt2out2('out2.txt', 'OR :MEM_REG_META_TB:$10 :MEM_REG_META_TB:$10 0x8000')
  Writetxt2out2('out2.txt', 'WRW :REG_META_TB:0x00002000 :MEM_REG_META_TB:$10')

  Writetxt2out2('out2.txt', '\n-- enable window 15, allow all of register region (linear 0x02000000-0x02FFFFFF)')
  Writetxt2out2('out2.txt', 'WRW :REG_META_TB:0x00002310 0x00000000')
  Writetxt2out2('out2.txt', 'WRW :REG_META_TB:0x00002320 0x00010000')
  Writetxt2out2('out2.txt', 'WRW :REG_META_TB:0x00002330 0x00FFFFFF')
  Writetxt2out2('out2.txt', 'WRW :REG_META_TB:0x00002340 0x00010000')

  Writetxt2out2('out2.txt', '\n-- enable string printing (must occur after segment setup)')
  Writetxt2out2('out2.txt', 'WRW :REG_JX:0x027FFFF4 0xFEED9011')
  Writetxt2out2('out2.txt', 'WRW :REG_META_TB:0x00003000 0x00000001')
  Writetxt2out2('out2.txt', 'WRW :REG_META_TB:0x00003010 0x007FFFF0')
  Writetxt2out2('out2.txt', 'WRW :REG_META_TB:0x00003020 0x00010000\n')

  return


###################################################
# Get the DCache size by reading the CORE_CONFIG2 register.
#
# DCacheGetSize <none>
###################################################
def DCacheGetSize() :
  metac_id = Target.MemRead(":REGMETA: 0x04830000")
  major_ver = (metac_id >> 24) & 0xFF
  size = 0

  if major_ver >= 2 :
    # CORE_CONFIG2 register, containing DCACHE_SIZE and DCACHE_NP fields is
    # present

    core_config2 = Target.MemRead(":REGMETA: 0x04831020")
    size_bits = (core_config2 >> 16) & 7

    if size_bits > 5 :
      # TRM has values 6, 7 as reserved, so signal an error
      print "Minibench: Error: Invalid DCache size read from CORE_CONFIG2 register"
    else :
      # size_bits == 0 corresponds to  4KB    (DCACHE_SMALL == 0)
      #                               64Bytes (DCACHE_SMALL == 1)
      size = 1 << (12 + size_bits)

      # Check if DCACHE_SMALL is set.
      small_bit = (core_config2 >> 26) & 1
      if small_bit != 0 :
        size = size >> 6

  return size


###################################################
# Purge the data cache (for write-back caches only)
# DCachePurge <none>
###################################################
def DCachePurge() :
  # Cache purge - required for Garten (writeback caches) only
  txt = '\n-- Purge Data Cache'
  Writetxt2out2('out2.txt', txt)

  txt = '--   Purge thread 0 local and global partitions'
  Writetxt2out2('out2.txt', txt)
  txt = 'WRW :REG_JX:0x04830050 0x00000018'
  Writetxt2out2('out2.txt', txt)
  Target.MemWrite(":REGMETA:" + "0x04830050", "0x00000018");

  txt = '\n--   Purge thread 1 local partition'
  Writetxt2out2('out2.txt', txt)
  txt = 'WRW :REG_JX:0x04830058 0x00000010'
  Writetxt2out2('out2.txt', txt)
  Target.MemWrite(":REGMETA:" + "0x04830058", "0x00000010");

  txt = '\n--   Purge thread 2 local partition'
  Writetxt2out2('out2.txt', txt)
  txt = 'WRW :REG_JX:0x04830060 0x00000010'
  Writetxt2out2('out2.txt', txt)
  Target.MemWrite(":REGMETA:" + "0x04830060", "0x00000010");

  txt = '\n--   Purge thread 3 local partition'
  Writetxt2out2('out2.txt', txt)
  txt = 'WRW :REG_JX:0x04830068 0x00000010'
  Writetxt2out2('out2.txt', txt)
  Target.MemWrite(":REGMETA:" + "0x04830068", "0x00000010")

  txt = '\n--   Poll for flushes to complete'
  Writetxt2out2('out2.txt', txt)
  txt = 'POL :REG_JX:0x04830048 0 0xFFFFFFFF 0 50 200'
  Writetxt2out2('out2.txt', txt)
  Target.MemPol(":REGMETA:" + "0x04830048", "0x00000000", "0x00000001", 0, 1);


###################################################
# Flush the data cache given it's size in bytes
# DCacheFlush <size> 
###################################################
def DCacheFlush(size, out2) :
  if out2 != 0 :
    txt = '\n-- Flush Data Cache: Size 0x' + toHex(size) + ' bytes'
    Writetxt2out2('out2.txt', txt)

  # base = LINSYSCFLUSH_DCACHE_LINE
  base = 0x04400000
  offset = 0

  while (offset < size) :
    addr = '0x' + toHex(base + offset)

    if out2 != 0 :
      txt = 'WRW :REG_JX:' + addr + ' 0x00000000'
      Writetxt2out2('out2.txt', txt)

    Target.MemWrite(":REGMETA:" + addr, '0x00000000')
    offset += 64


###################################################
# RWR
# RWR :<offset>:<address> <mask> <data> 
###################################################
def RWR(addr, mask, data) :
  print "Needs Implementation"
  sys.exit(2)
  

###################################################
# MRD
# MRD :<offset
###################################################
def MRD(addr) :
  print "Needs Implementation"
  sys.exit(2)


###################################################
# USR
# USR <value1> <value2> <value3> <value4> 
###################################################
def USR(value1, value2, value3, value4) :
  print "Needs Implementation"
  sys.exit(2)


###############################################################################
#
# SetupMb(targ, progrep, mtx)
#
# Setup Minibench
#
# targ
# progrep
#
###############################################################################

def SetupMb(progrep, mtx=0) :

  global Progress
  global Mtx
  global TxrxdtAddr
  global TxrxrqAddr

  # Flag whether target is MTX or not
  Mtx = mtx

  # Variable to report progress to the console
  Progress = progrep

  if Mtx != 0:
    TxrxdtAddr = '000000F8'
    TxrxrqAddr = '000000FC'

  return

# End of Microbench.py
