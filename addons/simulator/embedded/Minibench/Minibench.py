#*****************************************************************************
#
#               file : $RCSfile: Minibench.py,v $
#             author : $Author: ral $
#  date last revised : $Date: 2012/10/24 11:20:06 $
#    current version : $Revision: 1.85 $
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
A0Uspecifier = '00000003'
PCUspecifier = '00000005'

# TXENABLE addresses
T0ENABLE = '04800000'
T1ENABLE = '04801000'
T2ENABLE = '04802000'
T3ENABLE = '04803000'

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


###############################################################################
#
# RegWrite(dest, data)
#
# Write DWORD to address
#
# dest META address to write value to
# data Value to write
#
###############################################################################

def RegWrite(dest, data) :

  if (long(dest, 16) >= long('0x87FFFF00',16) ) & \
     (long(dest, 16) <  long('0x88000000',16) ) :
    if Progress == 1 :
      txt = 'Minibench: RegWrite discarding DA special address: ' + dest + ', ' + data
      print txt

  else:
    addr = ":REGMETA:" + dest

    fout2 = open('tmpregs2out2.txt', 'a')

    if dest.startswith('0x') or dest.startswith('0X'):
      dest = dest[2:]

    txregs = [T0ENABLE, T1ENABLE, T2ENABLE, T3ENABLE, TxrxrqAddr, TxrxdtAddr]
    l2regs = [SYSC_L2C_INIT, SYSC_L2C_ENABLE]

    # Log the write to be added to the out2 script
    if (dest not in txregs) and (dest not in l2regs) and                                                                       \
       not((long (dest, 16) >= long (segBase,  16)) and (long (dest, 16) < (long (segBase,  16) + (64 * (maxSegs + 1))))) and \
       not((long (dest, 16) >= long (ebwcCrtl, 16)) and (long (dest, 16) < (long (ebwcCrtl, 16) + ( 8 * 4           ))))  :
      p = re.compile(r"^0[0-9a-fA-F]+$")
      if len(dest) == 8 and p.match(dest) :
        txt = 'MM ' + dest + '\n'
        fout2.write(txt)

    fout2.close()

    # Check for any segment mmu & L2 writes (from LDLK), as the testbenches manage these for themselves
    if (dest not in l2regs) and                                                                                         \
       not((long (dest, 16) >= long (segBase, 16)) and (long (dest, 16) < (long (segBase, 16) + (64*(maxSegs+1))))) and \
       not((long (dest, 16) >= long (ebwcCrtl,16)) and (long (dest, 16) < (long (ebwcCrtl,16) + (8*4           )))) :
      if Progress == 1 :
        txt = 'Minibench: RegWrite setting register: ' + dest + ', ' + data
        print txt
      Target.MemWrite(addr, data)

  return


###############################################################################
#
# MtxRegWrite(dest, data)
#
# Write DWORD to MTX control interface.
# Based on RegWrite, with no logic to ignore certain addresses (eg. DA magic
# addresses) and writes to MTX specific namespace.
#
# Need to check what CSim supports
#
# dest MTX address to write value to
# data Value to write
#
###############################################################################

def MtxRegWrite(dest, data) :

  addr = ":REG_MTX:" + dest

  fout2 = open('tmpregs2out2.txt', 'a')

  if dest.startswith('0x') or dest.startswith('0X'):
    dest = dest[2:]

  # Do we need this filter here?
  #txregs = [T0ENABLE, T1ENABLE, T2ENABLE, T3ENABLE, TxrxrqAddr, TxrxdtAddr]

  # Log the write to be added to the out2 script
  # Don't think we need this either
  #if (dest not in txregs) \
  #    and not( ( long(dest,16) >= long(segBase,16)) and ( long(dest,16) < (long(segBase,16) + (64*(maxSegs+1))) ) ) \
  #    and not( ( long(dest,16) >= long(ebwcCrtl,16)) and ( long(dest,16) < (long(ebwcCrtl,16) + (8*4)) ) )       :
  p = re.compile(r"^0[0-9a-fA-F]+$")
  if len(dest) == 8 and p.match(dest) :
    txt = 'MM ' + dest + '\n'
    fout2.write(txt)

  fout2.close()

  if Progress == 1 :
    txt = 'Minibench: MtxRegWrite setting register: ' + dest + ', ' + data
    print txt
  Target.MemWrite(addr, data)

  return


###################################################
# Write DWORD to address
# RegWriteMemSetup <address> <data>
# Called from Memory Setup scripts where direct access to control regs is required
# (Workaround for LDLK issues)
###################################################
def RegWriteMemSetup(dest, data) :

# print "Addr:"+dest+" , data:"+data+"\n" 
  if Progress == 1 :
    txt = 'Minibench: RegWriteMemSetup setting register: ' + dest + ', ' + data
    print txt

  txt = 'WRW :REG_JX:' + dest + ' ' + data
  Writetxt2out2(txt)

  addr = ":REGMETA:" + dest

  Target.MemWrite(addr, data)

  return


###################################################
# Read DWORD from address
# RegRead <address>
###################################################    
def RegRead(dest) :
  
  addr = ":REGMETA:" + dest
  
  val = Target.MemRead(addr)
    
  return val


###################################################
# Read DWORD from address
# MtxRegRead <address>
###################################################    
def MtxRegRead(dest) :
  
  addr = ":REG_MTX:" + dest
  
  val = Target.MemRead(addr)
    
  return val


###################################################
# Poll address for data
# RegPol <address> <value> [<mask> [<operator> [<ntimes>]]]
###################################################    
def RegPol(dest, value, mask="FFFFFFFF", operator=0, ntimes=1) :

  addr = ":REGMETA:" + dest

  # Call the target Pol functions according to the default arguments
  # CSIM : dest, value, mask="FFFFFFFF", operator=0, ntimes=1
  # FPGA : dest, value, mask="FFFFFFFF", operator=0, ntime=int("0FFFFFFF", 16)

  if ntimes == 1 : 
    Target.MemPol(addr, value, mask, operator)
  else : 
    Target.MemPol(addr, value, mask, operator, ntimes)

  return


###################################################
# Poll address for data
# MtxRegPol <address> <value> <mask> <time>
# Based on RegWrite, targets MTX specific namespace; need to check what CSim supports
###################################################    
def MtxRegPol(dest, value, mask="FFFFFFFF", operator=0, ntimes=1) :

  addr = ":REG_MTX:" + dest

  # Call the target Pol functions according to the default arguments
  # CSIM : dest, value, mask="FFFFFFFF", operator=0, ntimes=1
  # FPGA : dest, value, mask="FFFFFFFF", operator=0, ntime=int("0FFFFFFF", 16)

  if ntimes == 1 : 
    Target.MemPol(addr, value, mask, operator)
  else : 
    Target.MemPol(addr, value, mask, operator, ntimes)

  return


###################################################
# Write DWORD to slave port
# SlaveWrite <offset> <data>
###################################################
def SlaveWrite(dest, data) :

  addr = ":REG_SLVDBG:" + dest

  Target.MemWrite(addr, data)

  return


###################################################
# Read DWORD from slave port
# SlaveRead <offset>
###################################################    
def SlaveRead(dest) :

  addr = ":REG_SLVDBG:" + dest

  val = Target.MemRead(addr)

  return val


###################################################
# Poll slave port for data
# SlavePol <offset> <value> <mask> <time>
###################################################    
def SlavePol(dest, value, mask="FFFFFFFF", operator=0, ntimes=1) :

  addr = ":REG_SLVDBG:" + dest

  if ntimes == 1 : 
    Target.MemPol(addr, value, mask, operator)
  else : 
    Target.MemPol(addr, value, mask, operator, ntimes)

  return

################################################################################
#
# ResetTXUXXRXRegs
#
################################################################################

def ResetTXUXXRXRegs (Thread, IsMtx) :
  """Reset the TXUXXRXRQ and TXUXXRXDT registers back to their reset values.

  This relies on the fact that the unit specifier of 0 is actually to the
  DaOpPaMe template registers, so writing to to Template register 0 on thread 0
  should get the values to their reset state.

  Returns:
  """
  if Thread in [1, 2, 3, 4] :
    # Restore TXUXXRXRQ's reset value to CSim & VHDL
    Writetxt2out2('-- Restore TXUXXRXRQ reset value')

    if IsMtx == 0:
      # Pol TxrxrqAddr to make sure last transaction completed
      RegPol(TxrxrqAddr, '80000000', '80000000', 0)
      # Reset TxrxrqAddr
      RegWrite(TxrxrqAddr, '80000000')
    else:
      # Pol TxrxrqAddr to make sure last transaction completed
      MtxRegPol(TxrxrqAddr, '80000000', '80000000', 0)
      # Reset TxrxrqAddr
      MtxRegWrite(TxrxrqAddr, '80000000')

    txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x80000000'
    Writetxt2out2(txt)
    Writetxt2out2('')

###################################################
# Print comment
# COM <Comment>
###################################################    
def Com(strLine) :
  
  Target.Com(strLine)

  return


###################################################
# Print Progress to console&/out2.txt
# RepProg <Comment>
###################################################    
def RepProg(strLine) :
  
  if Progress == 1:
    txt = '\n' + ' TestProgress: -- ' + strLine
    print txt
    
  if strLine == 'Configure Registers' :
    fout2 = open('tmpregs2out2.txt', 'a') 

    txt = '\n-- ' + strLine + '\n'
    fout2.write(txt)

    # Core & exp priv regs for all threads
    txt = 'MM 04810100\n'
    fout2.write(txt)
    txt = 'MM 04810108\n'
    fout2.write(txt)
    txt = 'MM 04810110\n'
    fout2.write(txt)
    txt = 'MM 04810118\n'
    fout2.write(txt)
    
    # Direct map addrs 0 to 3
    txt = 'MM 04830080\n'
    fout2.write(txt)
    txt = 'MM 04830090\n'
    fout2.write(txt)
    txt = 'MM 048300a0\n'
    fout2.write(txt)
    txt = 'MM 048300b0\n'
    fout2.write(txt)

    # TXDIVTIME
    txt = 'MM 048000e0\n'
    fout2.write(txt)
    txt = 'MM 048010e0\n'
    fout2.write(txt)
    txt = 'MM 048020e0\n'
    fout2.write(txt)
    txt = 'MM 048030e0\n'
    fout2.write(txt)
      
    fout2.close()
    
    
  return


###################################################
# Load the DNL onto the target
# LoadDnl <out.dnl>
###################################################    
def LoadDnl(dnlfile) :
  
  fout2 = open('tmpregs2out2.txt', 'a')  
  txt = '\n-- DNL ' + dnlfile + '\n'
  fout2.write(txt)
  fout2.close()

  import Dnl
  
  Dnl.WriteFile(Target, dnlfile)
  
  return


###############################################################################
#
# MemDump(base, dumplen, fname)
#
# Dump memory binaries.
# Uses Mtx global flag
#
# base    Base address to start dump from
# dumplen Length of memory (bytes) to dump
# fname   Name of file to place dump in
#
###############################################################################

def MemDump(base, dumplen, fname):

  if Mtx == 0:
    # Save the Cache and MMU states before dump
    SYSC_DCPART0 = Target.MemRead(Sys_Dc0)
    SYSC_DCPART1 = Target.MemRead(Sys_Dc1)
    SYSC_DCPART2 = Target.MemRead(Sys_Dc2)
    SYSC_DCPART3 = Target.MemRead(Sys_Dc3)
    SYSC_ICPART0 = Target.MemRead(Sys_Ic0)
    SYSC_ICPART1 = Target.MemRead(Sys_Ic1)
    SYSC_ICPART2 = Target.MemRead(Sys_Ic2)
    SYSC_ICPART3 = Target.MemRead(Sys_Ic3)
  
    # Save MMU CACHE Enable Value
    MmuCacheEnable = Target.MemRead(Sys_CM_Config)
  
    # Disable/Enable/Disable the MMU (and caches)
    Target.MemWrite(Sys_CM_Config, "0x00000000")
    Target.MemWrite(Sys_CM_Config, toHex(MmuCacheEnable))
    Target.MemWrite(Sys_CM_Config, "0x00000000")

    # Save MMCU_TABLE_PHYS Value
    MmuTableBase = Target.MemRead(Mmcu_Table_Phys)
  
  # Dump memory binary file
  Dump(base, dumplen, fname)

  if Mtx == 0:  
    # Restore MMCU_TABLE_PHYS Value
    Target.MemWrite(Mmcu_Table_Phys, toHex(MmuTableBase))
  
    # Validate MMU RAM Cache
    Target.MemWrite(LinSysCflush_Mmcu, "0x00000000")
    Target.MemWrite(Sys_CM_Config, toHex(MmuCacheEnable))
    Target.MemWrite(LinSysCflush_Mmcu, "0x00000000")
  
    # Restore Cache partitioning masks
    Target.MemWrite(Sys_Dc0, toHex(SYSC_DCPART0))
    Target.MemWrite(Sys_Dc1, toHex(SYSC_DCPART1))
    Target.MemWrite(Sys_Dc2, toHex(SYSC_DCPART2))
    Target.MemWrite(Sys_Dc3, toHex(SYSC_DCPART3))
    Target.MemWrite(Sys_Ic0, toHex(SYSC_ICPART0))
    Target.MemWrite(Sys_Ic1, toHex(SYSC_ICPART1))
    Target.MemWrite(Sys_Ic2, toHex(SYSC_ICPART2))
    Target.MemWrite(Sys_Ic3, toHex(SYSC_ICPART3))
  
    # Enable and Flush Caches
    Target.MemWrite(IcFlush, "0x00000001")
    Target.MemWrite(DcFlush, "0x00000001")
    Target.MemWrite(IcEnable, "0x00000001")
    Target.MemWrite(DcEnable, "0x00000001")
  
  return
  

###############################################################################
#
# Dump(base, length, filename)
#
# Perform the Dump
#
# base     Base address to start dump from
# length   Length of memory (bytes) to dump
# filename Name of file to place dump in
# 
###############################################################################


def Dump(base, length, filename):
  From = int(base,16)
  Len = int(length,16)

  if Progress == 1:
    print "\tDumping %s from 0x%08x for 0x%08x bytes" %(filename, From, Len)

  FromAddr = (From / 4) * 4
  NumToRead = (Len / 4) * 4
  if NumToRead < Len :
    NumToRead += 4 # round up

  CallAddr = toHex(FromAddr)
  Target.SAB(filename, CallAddr, NumToRead)

  return


###################################################
# Gives the hexadecimal representation of an integer
# toHex <num>
###################################################
def toHex(num) :
  return "%08X" %num


###############################################################################
#
# RegDump2out2(threads, threadsmask, thrdstate, start_intrusive, out2polls)
#
# Process the tmpregs2out2 file and dump the registers to out2.txt
# Uses Mtx global flag
#
# threads     
# threadsmask 
# thrdstate       0(start)/1(stop)
# start_intrusive 0(don't)/1(do)
# out2polls
#
###############################################################################

def RegDump2out2(threads, threadsmask, thrdstate, start_intrusive, out2polls) :
  
  RegConfigfname = 'tmpregs2out2.txt'
  
  # Check if we are at the threads stopped state
  if thrdstate == 1 and os.path.isfile(os.path.abspath(RegConfigfname)) :

    # Out2 poll for test end
    txt = '\n-- Poll for Test End (allows ' + str(out2polls * 20000) + ' cycles)'
    Writetxt2out2(txt)
    if ( threadsmask & 1 ) != 0 :
      txt = 'POL :REG_JX:0x' + T0ENABLE + ' 0x00000000 0x00000001 0 ' + str(out2polls) + ' 20000'
      Writetxt2out2(txt)
    if ( threadsmask & 2 ) != 0 :
      txt = 'POL :REG_JX:0x' + T1ENABLE + ' 0x00000000 0x00000001 0 ' + str(out2polls) + ' 20000'
      Writetxt2out2(txt)
    if ( threadsmask & 4 ) != 0 :
      txt = 'POL :REG_JX:0x' + T2ENABLE + ' 0x00000000 0x00000001 0 ' + str(out2polls) + ' 20000'
      Writetxt2out2(txt)
    if ( threadsmask & 8 ) != 0 :
      txt = 'POL :REG_JX:0x' + T3ENABLE + ' 0x00000000 0x00000001 0 ' + str(out2polls) + ' 20000'
      Writetxt2out2(txt)

    # Check for core specific script and emit additional out2 setup before we poll the threads
    if os.path.exists("Core.py") :
      import Core
      Core.Regs2out2end()

    # Check for test specific script and emit additional out2 setup before we poll the threads
    if os.path.exists("TestCfg.py") :
      import TestCfg
      TestCfg.Regs2out2end()

    Writetxt2out2('\n-- Poll PC and A0 end state for all threads') 
    if ( threadsmask & 1 ) != 0 :
      Writetxt2out2('-- Poll Thread 0 PC and A0 end state')

      # Check the thread 0 A0 value
      T0A0 = toHex( long(A0Uspecifier, 16) | long(T0specifier, 16) )
      readVal = ProcessCoreRead(T0A0, 1)
      txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + toHex( long(T0A0, 16) | long(TxrxrqReadbit, 16) )
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxdtAddr + ' 0x' + readVal + ' 0xFFFFFFFF 0 50 200'
      Writetxt2out2(txt)

      # Check the thread 0 PC value
      T0PC = toHex( long(PCUspecifier, 16) | long(T0specifier, 16) )
      readVal = ProcessCoreRead(T0PC, 1)
      txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + toHex( long(T0PC, 16) | long(TxrxrqReadbit, 16) )
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxdtAddr + ' 0x' + readVal + ' 0xFFFFFFFF 0 50 200'
      Writetxt2out2(txt)

    if ( threadsmask & 2 ) != 0 :
      Writetxt2out2('-- Poll Thread 1 PC and A0 end state')

      # Check the thread 1 A0 value
      T1A0 = toHex( long(A0Uspecifier, 16) | long(T1specifier, 16) )
      readVal = ProcessCoreRead(T1A0, 1)
      txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + toHex( long(T1A0, 16) | long(TxrxrqReadbit, 16) )
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxdtAddr + ' 0x' + readVal + ' 0xFFFFFFFF 0 50 200'
      Writetxt2out2(txt)

      # Check the thread 1 PC value
      T1PC = toHex( long(PCUspecifier, 16) | long(T1specifier, 16) )
      readVal = ProcessCoreRead(T1PC, 1)
      txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + toHex( long(T1PC, 16) | long(TxrxrqReadbit, 16) )
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxdtAddr + ' 0x' + readVal + ' 0xFFFFFFFF 0 50 200'
      Writetxt2out2(txt)

    if ( threadsmask & 4 ) != 0 :
      Writetxt2out2('-- Poll Thread 2 PC and A0 end state')

      # Check the thread 2 A0 value
      T2A0 = toHex( long(A0Uspecifier, 16) | long(T2specifier, 16) )
      readVal = ProcessCoreRead(T2A0, 1)
      txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + toHex( long(T2A0, 16) | long(TxrxrqReadbit, 16) )
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxdtAddr + ' 0x' + readVal + ' 0xFFFFFFFF 0 50 200'
      Writetxt2out2(txt)

      # Check the thread 2 PC value
      T2PC = toHex( long(PCUspecifier, 16) | long(T2specifier, 16) )
      readVal = ProcessCoreRead(T2PC, 1)
      txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + toHex( long(T2PC, 16) | long(TxrxrqReadbit, 16) )
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxdtAddr + ' 0x' + readVal + ' 0xFFFFFFFF 0 50 200'
      Writetxt2out2(txt)

    if ( threadsmask & 8 ) != 0 :
      Writetxt2out2('-- Poll Thread 3 PC and A0 end state')

      # Check the thread 3 A0 value
      T3A0 = toHex( long(A0Uspecifier, 16) | long(T3specifier, 16) )
      readVal = ProcessCoreRead(T3A0, 1)
      txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + toHex( long(T3A0, 16) | long(TxrxrqReadbit, 16) )
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxdtAddr + ' 0x' + readVal + ' 0xFFFFFFFF 0 50 200'
      Writetxt2out2(txt)

      # Check the thread 3 PC value
      T3PC = toHex( long(PCUspecifier, 16) | long(T3specifier, 16) )
      readVal = ProcessCoreRead(T3PC, 1)
      txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + toHex( long(T3PC, 16) | long(TxrxrqReadbit, 16) )
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)
      txt = 'POL :REG_JX:0x' + TxrxdtAddr + ' 0x' + readVal + ' 0xFFFFFFFF 0 50 200'
      Writetxt2out2(txt)

    ResetTXUXXRXRegs (threads, Mtx)

    os.remove(os.path.abspath(RegConfigfname))

  # If we are at the threads start state then dump Registers to out2.txt
  elif thrdstate == 0 and os.path.isfile(os.path.abspath(RegConfigfname)) :

    Writetxt2out2('')

    if Mtx == 1:
      # Add TXSTATUS to the list of registers to dump
      fout2 = open('tmpregs2out2.txt', 'a')
      fout2.write('MM 04800008\n')
      fout2.close()

    fdumpregs = open(os.path.abspath(RegConfigfname), 'r')

    for line in fdumpregs :
      line = line.strip()
      if line :
        tmpline = line
        cmd = (tmpline.split())[0]

        if cmd == '--' :
          Writetxt2out2(line)
        elif cmd == 'MM' :
          ProcessRegRead(line)
        else :
          continue

    fdumpregs.close()

    # Check for core specific script and invoke additional out2 registers setup before we start the threads running
    if os.path.exists("Core.py") :
      import Core
      Core.Regs2out2start()

    # Check for test specific script and invoke additional out2 registers setup before we start the threads running
    if os.path.exists("TestCfg.py") :
      import TestCfg
      TestCfg.Regs2out2start()

    Writetxt2out2('')

    # Setup Threads in out2.txt
    if ( threadsmask & 1 ) != 0 :
      Writetxt2out2('-- Set up Thread 0')

      # Dump the thread 0 A0 value
      T0A0 = toHex( long(A0Uspecifier, 16) | long(T0specifier, 16) )
      ProcessCoreRead(T0A0)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)

      # Dump the thread 0 PC value
      T0PC = toHex( long(PCUspecifier, 16) | long(T0specifier, 16) )
      ProcessCoreRead(T0PC)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)
      Writetxt2out2('')

    if ( threadsmask & 2 ) != 0 :
      Writetxt2out2('-- Set up Thread 1')

      # Dump the thread 1 A0 value
      T1A0 = toHex( long(A0Uspecifier, 16) | long(T1specifier, 16) )
      ProcessCoreRead(T1A0)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)

      # Dump the thread 1 PC value
      T1PC = toHex( long(PCUspecifier, 16) | long(T1specifier, 16) )
      ProcessCoreRead(T1PC)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)
      Writetxt2out2('')

    if ( threadsmask & 4 ) != 0 :
      Writetxt2out2('-- Set up Thread 2')

      # Dump the thread 2 A0 value
      T2A0 = toHex( long(A0Uspecifier, 16) | long(T2specifier, 16) )
      ProcessCoreRead(T2A0)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)

      # Dump the thread 2 PC value
      T2PC = toHex( long(PCUspecifier, 16) | long(T2specifier, 16) )
      ProcessCoreRead(T2PC)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)
      Writetxt2out2('')

    if ( threadsmask & 8 ) != 0 :
      Writetxt2out2('-- Set up Thread 3')

      # Dump the thread 3 A0 value
      T3A0 = toHex( long(A0Uspecifier, 16) | long(T3specifier, 16) )
      ProcessCoreRead(T3A0)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)

      # Dump the thread 3 PC value
      T3PC = toHex( long(PCUspecifier, 16) | long(T3specifier, 16) )
      ProcessCoreRead(T3PC)
      txt = 'POL :REG_JX:0x' + TxrxrqAddr + ' 0x80000000 0x80000000 0 50 200'
      Writetxt2out2(txt)
      Writetxt2out2('')

    ResetTXUXXRXRegs (threads, Mtx)

    # Start Threads
    Writetxt2out2('-- Start Threads')

    # First set lock2 (and intrusive if need)
    MDbgCtrl1Val = long(DbgCtrl1_Lock2, 16)

    if start_intrusive == 1 :
      MDbgCtrl1Val |= long(DbgCtrl1_Intrusive, 16)

    txt = 'WRW :REG_JD:' + MDbgCtrl1Addr + ' 0x' + toHex(MDbgCtrl1Val)
    Writetxt2out2(txt)
    txt = 'POL :REG_JD:' + MDbgCtrl1Addr + ' ' + DbgCtrl1_Lock2Lock + ' ' + DbgCtrl1_Lock2Lock + ' 0 50 200'
    Writetxt2out2(txt)

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
    Writetxt2out2(txt)

  else :
    txt = 'Register Dump configuration file ' + RegConfigfname + ' not found'
    print txt
    sys.exit(2)
  
  return


###################################################
# Write text in out2.txt
# Writetxt2out2 <line>
###################################################
def Writetxt2out2(line) :
  fout2 = open('out2.txt', 'a')
  str = line + '\n'
  fout2.write(str)
  fout2.close()
  return


###################################################
# Read Reg and write to out2.txt
# ProcessRegRead <line>
###################################################
def ProcessRegRead(line) :
  strline = line
  dest = strline.split()[1]
  data = toHex(RegRead(dest))
  fout2 = open('out2.txt', 'a')
  txt = 'WRW :REG_JX:0x' + dest + ' 0x' + data + '\n'
  fout2.write(txt)
  fout2.close()
  return


###############################################################################
#
# ProcessCoreRead(readaddr, quiet=0)
#
# Read Core reg and write to out2.txt
#
# readaddr
# quiet
#
###############################################################################

def ProcessCoreRead(readaddr, quiet=0) :
  # strline = line
  # readaddr = strline.split()[1]
  data = toHex( long(readaddr, 16)  | long(TxrxrqReadbit, 16) )

  # Write the Core Reg address to TxrxrqAddr
  if Mtx == 0:
    RegWrite(TxrxrqAddr, data)
  else:
    MtxRegWrite(TxrxrqAddr, data)
  
  # Pol TxrxrqAddr if the value is available in TxrxdtAddr
  if Mtx == 0:
    RegPol(TxrxrqAddr, '80000000', '80000000', 0)
  else:
    MtxRegPol(TxrxrqAddr, '80000000', '80000000', 0)
  
  # Read the value from TxrxdtAddr
  if Mtx == 0:
    rawread = RegRead(TxrxdtAddr)
  else:
    rawread = MtxRegRead(TxrxdtAddr)

  readVal = toHex(rawread)

  if not quiet :
    fout2 = open('out2.txt', 'a')
    txt = 'WRW :REG_JX:0x' + TxrxdtAddr + ' 0x' + readVal + '\n'
    fout2.write(txt)
    txt = 'WRW :REG_JX:0x' + TxrxrqAddr + ' 0x' + readaddr + '\n'
    fout2.write(txt)
  
    fout2.close()
  
  return readVal


###################################################
# Write Start threads command to out2.txt
# ProcessStThd <TXENABLE>
###################################################
def ProcessStThd(txenable) :
  strline = txenable
  #str = strline.split()[1:]

  fout2 = open('out2.txt', 'a')
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

def Out2MemSetup(memtype, strtaddr, addrlen ) :

  # Memory type - External memory
  if memtype == 0 :
    if Progress == 1 :
      print "\nSetting up external memory"
    Writetxt2out2('\n-- Base address for external memory')
    txt = 'MOV :MEM_META_MAIN:$1 ' + strtaddr + '\n'
    Writetxt2out2(txt)
    Writetxt2out2('-- Set external memory start address')
    Writetxt2out2('WRW :REG_META_TB:0x00000250 :MEM_META_MAIN:$1\n')
    txt = 'MALLOC :MEM_META_MAIN:EXT0 ' + addrlen + ' 0x00800000'
    Writetxt2out2(txt)

  # Memory type - CoreCode memory
  if memtype == 1 :
    if Progress == 1 :
      print "\nSetting up CoreCode memory"
    txt = '\nMALLOC :MEM_META_CCM:CORECODE ' + addrlen + ' 0x4'
    Writetxt2out2(txt)

  # Memory type - CoreData memory
  if memtype == 2 :
    if Progress == 1 :
      print "\nSetting up CoreData memory"
    txt = '\nMALLOC :MEM_META_CDM:COREDATA ' + addrlen + ' 0x4'
    Writetxt2out2(txt)

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
    Writetxt2out2(txt)
    memsize = long('0x00008000', 16)
    curofs = 0
    while ( curofs < long(addrlen, 16) ) :
      memno = str( curofs / memsize )
      if Progress == 1 :
        txt = '   Core Code memory ' + memno + ' at offset 0x%08X bytes' %curofs
        print txt
      txt = 'MALLOC :MEM_MTX_CM_' + memno +':CORECODE 0x' + toHex(memsize) + ' 0x4'
      Writetxt2out2(txt)
      curofs += memsize
    if Progress == 1 :
      print "   ..done"

  else:
    print "Minibench: Error: MTX core memory invalid memory type"

  if Progress == 1 :
    print ""

  return


###############################################################################
#
# Out2Memdump(memtype, strtaddr, addrlen, thrdst)
#
# Dump the memory in out2.txt
#
# memtype (0-ext/1-corecode/2-coredata)
# strtaddr
# addrlen
# thrdst (0-strt/1-end)
#
###############################################################################

def Out2Memdump(memtype, strtaddr, addrlen, thrdst) :

  # Check if the threads are at their start state
  if thrdst == 0 :

    # Memory type - External memory
    if memtype == 0 :
      if Progress == 1:
        print "\nDumping External memory start state"
      txt = '\n-- Start state External memory'
      Writetxt2out2(txt)
      MemDump(strtaddr, addrlen, 'Ext-st.bin')
      txt = 'LDB :MEM_META_MAIN:EXT0:0x0 ' + addrlen + ' 0x00000000 Ext-st.bin\n'
      Writetxt2out2(txt)

    # Memory type - CoreCode memory
    if memtype == 1 :
      if Progress == 1:
        print "\nDumping CoreCode memory start state"
      txt = '\n-- Start state CoreCode memory'
      Writetxt2out2(txt)
      MemDump(strtaddr, addrlen, 'CoreCode-st.bin')
      txt = 'LDB :MEM_META_CCM:CORECODE:0x0 ' + addrlen + ' 0x00000000 CoreCode-st.bin\n'
      Writetxt2out2(txt)

    # Memory type - CoreData memory
    if memtype == 2 :
      if Progress == 1:
        print "\nDumping CoreData memory start state"
      txt = '\n-- Start state CoreData memory'
      Writetxt2out2(txt)
      MemDump(strtaddr, addrlen, 'CoreData-st.bin')
      txt = 'LDB :MEM_META_CDM:COREDATA:0x0 ' + addrlen + ' 0x00000000 CoreData-st.bin\n'
      Writetxt2out2(txt)

  # Check if the threads are at their end state
  elif thrdst == 1 :

    # Memory type - External memory
    if memtype == 0 :
      if Progress == 1:
        print "\nDumping External memory end state"
      txt = '\n-- Check end state External memory'
      Writetxt2out2(txt)
      MemDump(strtaddr, addrlen, 'Ext-end.bin')
      txt = 'SAB :MEM_META_MAIN:EXT0:0x0 ' + addrlen + ' 0x00000000 Ext-end.bin\n'
      Writetxt2out2(txt)

    # Memory type - CoreCode memory
    if memtype == 1 :
      if Progress == 1:
        print "\nDumping CoreCode memory end state"
      txt = '\n-- Check end state CoreCode memory'
      Writetxt2out2(txt)
      MemDump(strtaddr, addrlen, 'CoreCode-end.bin')
      txt = 'SAB :MEM_META_CCM:CORECODE:0x0 ' + addrlen + ' 0x00000000 CoreCode-end.bin\n'
      Writetxt2out2(txt)

    # Memory type - CoreData memory
    if memtype == 2 :
      if Progress == 1:
        print "\nDumping CoreCode memory end state"
      txt = '\n-- Check end state CoreData memory'
      Writetxt2out2(txt)
      MemDump(strtaddr, addrlen, 'CoreData-end.bin')
      txt = 'SAB :MEM_META_CDM:COREDATA:0x0 ' + addrlen + ' 0x00000000 CoreData-end.bin\n'
      Writetxt2out2(txt)

  if Progress == 1:
    print ""

  return


###############################################################################
#
# Out2MtxCoreMemdump(memtype, strtaddr, addrlen, thrdst)
#
# Dump the MTX core memories in out2.txt
#
# memtype (1-corecode)
# strtaddr
# addrlen
# thrdst (0-strt/1-end)
#
# MTX organises core memories as adjacent blocks of 32KB
#
###############################################################################

def Out2MtxCoreMemdump(memtype, strtaddr, addrlen, thrdst) :

  if Progress == 1 :
    txt = '\nMTX memory dump, memory type %d at ' %memtype + strtaddr + ' for ' + addrlen + ' bytes, threadstate %d' %thrdst
    print txt

  # Check if the threads are at their start state
  if thrdst == 0 :

    # Memory type - CoreCode memory
    if memtype == 1 :
      if Progress == 1:
        print "MTX CoreCode memories start state"
      txt = '\n-- Start state MTX CoreCode memories'
      Writetxt2out2(txt)
      memsize = long('0x00008000', 16)
      curofs = 0
      while ( curofs < long(addrlen, 16) ) :
        memno = str( curofs / memsize )
        if Progress == 1 :
          txt = '   Core Code memory ' + memno + ' at offset 0x%08X bytes' %curofs
          print txt
        filename = 'CoreCode-st_' + memno + '.bin'
        MemDump( toHex( long(strtaddr,16) + curofs ), toHex(memsize), filename )
        txt = 'LDB :MEM_MTX_CM_' + memno +':CORECODE:0x0 0x' + toHex(memsize) + ' 0x00000000 ' + filename
        Writetxt2out2(txt)
        curofs += memsize

    else:
      print "Minibench: Error: MTX core memory invalid memory type"

  # Check if the threads are at their end state
  elif thrdst == 1 :

    # Memory type - CoreCode memory
    if memtype == 1 :
      if Progress == 1:
        print "MTX CoreCode memories end state"
      txt = '\n-- Check end state MTX CoreCode memories'
      Writetxt2out2(txt)
      memsize = long('0x00008000', 16)
      curofs = 0
      while ( curofs < long(addrlen, 16) ) :
        memno = str( curofs / memsize )
        if Progress == 1 :
          txt = '   Core Code memory ' + memno + ' at offset 0x%08X bytes' %curofs
          print txt
        filename = 'CoreCode-end_' + memno + '.bin'
        MemDump( toHex( long(strtaddr,16) + curofs ), toHex(memsize), filename )
        txt = 'SAB :MEM_MTX_CM_' + memno + ':CORECODE:0x0 0x' + toHex(memsize) + ' 0x00000000 ' + filename
        Writetxt2out2(txt)
        curofs += memsize

    else:
      print "Minibench: Error: MTX core memory invalid memory type"

  if Progress == 1:
    print ""

  return


###################################################
# Sets up default external memory: 32MB at 0xB0000000
# ExtMemDeclare
###################################################
def ExtMemDeclare() :
  global physMemPtr
  global physMemRem

  if Progress == 1:
    print "Minibench: acquiring default memory.."

  result =Target.SetExtMemIO ('0', '0xB0000000', '0x02000000')
  if result == 0:
#    physMemPtr = '0xB0000000'
#    physMemRem = '0x02000000'
    if Progress == 1:
      print "\t..OK"
  else :
    if Progress == 1:
      print "\t..failed; returned 0x%08x" %(result)

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
  
  pUser = Target.CreateExtMem ('0x0000000002000000', '32')  
  pCallback = Target.GetCallback(pUser)
  result =Target.MemPortDeclare (pUser, '0','0xFFFFFFFF70000000', '0x0000000030000000', \
    '0x0000000002000000', '32', 'SDRAM' ,pCallback)

  if result == 0:
    physMemPtr = '0xB0000000'
    physMemRem = '0x02000000'
    if Progress == 1:
      print "\t..OK"
  else :
    if Progress == 1:
      print "\t..failed; returned 0x%08x" %(result)

  return
  
def ExtMemCreate(size, width):
  """
  ExtMemCreate - Creates an external memory block of the given size and width.

  size  Size of the memory block to create in bytes.
  width Access width of the memory block in bits.

  Returns both the memory block handle and related callback function.
  """
  pUser = Target.CreateExtMem (size, width)
  pCallback = Target.GetCallback(pUser)

  return (pUser, pCallback)

def CoreMemRegister(memtype, strtaddr, size, Width, pUser, pCallback):
  """
  CoreMemRegister - Registers a block of memory as core memory.

  memtype   Type of core memory to register
            1 - core code memory
            2 - core data memory
  strtaddr  Base Meta address for the core memory.
  size      Size of the core memory block in bytes.
  Width     Access width for the block in bits.
  pUser     Pointer to previously created core memory block that is being registered.
  pCallback Callback function to pass in when registering the core memory block.
  """
  name = ''

  if memtype == 1 :
    name = 'Core Code'
    mask =  '0xFFFFFFFF82000000'
    match = '0x0000000080000000'
  elif memtype == 2:
    name = 'Core Data'
    mask =  '0xFFFFFFFF82000000'
    match = '0x0000000082000000'
  else:
    print "Error: Unknown memory type " + str(memtype)

  if name != '':
    if Progress == 1:
      print "\n"+name+" memories "
    result = Target.MemPortDeclare(pUser, memtype, mask, match, size, Width, \
                                   name, pCallback)

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
      if physMemRem < addrlen:
        print "           Error: Remaining physical memory too small for requested segment size"
      else:
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
  Writetxt2out2('\n-- Enable active windows')
  txt = 'WRW :REG_META_TB:0x00002000 ' + SegConfigBits
  Writetxt2out2(txt)

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
      Writetxt2out2(txt)

      segBaseAdr = '0x' + toHex(long(segBase, 16) + i*long('10', 16))
      segBaseVal = '0x' + toHex( (long(baseaddr[i], 16) & long('0xFFFFFFFF', 16) ) | segaccess[i] )
      txt = 'WRW :REG_JX:' + segBaseAdr + ' ' + segBaseVal
      Writetxt2out2(txt)
      # Write to the register in the simulator
      if Progress == 1:
        txt = '           writing base register:  0x' + toHex(long(segBaseAdr, 16)) + ', 0x' + toHex(long(segBaseVal, 16)) + ';'
        print txt
      Target.MemWrite(":REGMETA:" + segBaseAdr, segBaseVal);	

      segLimitAdr = '0x' + toHex(long(segLimit, 16) + i*long('10', 16))
      txt = 'WRW :REG_JX:' + segLimitAdr + ' 0x' + toHex(long(segLen[i],16)-1)
      Writetxt2out2(txt)
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
      Writetxt2out2(txt)
      if i < 10 :
        winnum = '0' + str(i)
      else :
        winnum = str(i)

      txt = 'MALLOC :MEM_META_WIN' + winnum + ':Seg' + winnum +'Adr ' + segLen[i] + ' 0x00001000'
      Writetxt2out2(txt)

      # Set the output address registers for this segment
      txt = '\n-- Set the output address registers for segment ' + str(i)
      Writetxt2out2(txt)
      txt = 'WRW :MEM_META_WIN' + winnum + ':$1 :MEM_META_WIN' + winnum + ':Seg' + winnum + 'Adr:0x0'
      Writetxt2out2(txt)
      txt = 'AND :MEM_META_WIN' + winnum + ':$2 :MEM_META_WIN' + winnum + ':$1 0xFFFFFFFF'
      Writetxt2out2(txt)
      txt = 'SHR :MEM_META_WIN' + winnum + ':$3 :MEM_META_WIN' + winnum + ':$1 32'
      Writetxt2out2(txt)
      txt = 'WRW :REG_JX:0x' + toHex(long(segOutA0, 16) + i*long('10', 16)) + ' :MEM_META_WIN' + winnum + ':$2'
      Writetxt2out2(txt)
      txt = 'WRW :REG_JX:0x' + toHex(long(segOutA1, 16) + i*long('10', 16)) + ' :MEM_META_WIN' + winnum + ':$3'
      Writetxt2out2(txt)

      #
      # Program test bench registers for this window
      # Code here also needs to read back the TB addresses for the segment and set [start|end][32|64]
      #
      winaddr = WinStart
      txt = '\n-- Program test bench registers for WIN' + str(i)
      Writetxt2out2(txt)
      # Setup the WIN register based on the segment MMU register settings
      txt = 'ADD :MEM_META_WIN' + winnum + ':$4 :MEM_META_WIN' + winnum + ':$1 0x' + toHex(long(segLen[i],16)-1) 
      Writetxt2out2(txt)
      # Setup the WIN register based on the segment MMU register settings
      txt = 'AND :MEM_META_WIN' + winnum + ':$5 :MEM_META_WIN' + winnum + ':$4 0xFFFFFFFF'
      Writetxt2out2(txt)
      txt = 'SHR :MEM_META_WIN' + winnum + ':$6 :MEM_META_WIN' + winnum + ':$4 32'
      Writetxt2out2(txt)
      winaddr = '0x' + toHex(long(winaddr, 16) + i*long('40', 16))
      # Value we need to read from the csim and put in start32[i]
      txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$2'
      Writetxt2out2(txt)
      winaddr = '0x' + toHex(long(winaddr, 16) + long('10', 16))
      # Value we need to read from the csim and put in start64[i]
      txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$3'
      Writetxt2out2(txt)
      winaddr = '0x' + toHex(long(winaddr, 16) + long('10', 16))
      # Value we need to read from the csim and put in end32[i]
      txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$5'
      Writetxt2out2(txt)
      winaddr = '0x' + toHex(long(winaddr, 16) + long('10', 16))
      # Value we need to read from the csim and put in end64[i]
      txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$6'
      Writetxt2out2(txt)

  # Flush writes to ensure segmmu & testbench setup complete
  txt = '\n-- Flush writes to ensure segmmu & testbench setup complete'
  Writetxt2out2(txt)
  txt = 'RDW :REG_JX:0x04800000'
  Writetxt2out2(txt)
  txt = 'RDW :REG_META_TB:0x00000000'
  Writetxt2out2(txt)

  txt = ''
  Writetxt2out2(txt)

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

  Writetxt2out2('\n-- Enable active windows')
  txt = 'WRW :REG_META_TB:0x00002000 ' + SegConfigBits
  Writetxt2out2(txt)

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
  Writetxt2out2(txt)

  segBaseAdr = '0x' + toHex(long(segBase, 16) + segID*long('10', 16))
  segBaseVal = '0x' + toHex( (long(baseaddr[winID], 16) & long('0xFFFFFFFF', 16) ) | segaccess[winID] )
  txt = 'WRW :REG_JX:' + segBaseAdr + ' ' + segBaseVal
  Writetxt2out2(txt)
  # Need to write to the register in simulator
  if Progress == 1:
    txt = '           writing base register:  0x' + toHex(long(segBaseAdr, 16)) + ', 0x' + toHex(long(segBaseVal, 16)) + ';'
    print txt
  Target.MemWrite(":REGMETA:" + segBaseAdr, segBaseVal);	

  segLimitAdr = '0x' + toHex(long(segLimit, 16) + segID*long('10', 16))
  txt = 'WRW :REG_JX:' + segLimitAdr + ' 0x' + toHex(long(segLen[winID],16)-1)
  Writetxt2out2(txt)
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
  Writetxt2out2(txt)

  # Window 11 should give us 0xB0000000, 16MB
  txt = 'MALLOC :MEM_META_WIN' + winnum + ':Seg' + winnum +'Adr ' + segLen[winID] + ' 0x00001000'
  Writetxt2out2(txt)

  # Check Window 11 gave us what we expect
  txt = '\n-- Check the address in window ' + winnum + ' is what we expect (read via TXCATCH1).'
  Writetxt2out2(txt)
  txt = 'WRW :REG_JX:0x04800088 :MEM_META_WIN' + winnum + ':Seg' + winnum + 'Adr:0x0'
  Writetxt2out2(txt)
  txt = 'POL :REG_JX:0x04800088 ' + str(baseaddr[winID]) + ' 0xFFFFFFFF 0'
  Writetxt2out2(txt)

  # Set the output address registers for segment 5
  txt = '\n-- Set the output address registers for segment ' + segnum
  Writetxt2out2(txt)
  txt = 'WRW :MEM_META_WIN' + winnum + ':$1 :MEM_META_WIN' + winnum + ':Seg' + winnum + 'Adr:0x0'
  Writetxt2out2(txt)
  txt = 'AND :MEM_META_WIN' + winnum + ':$2 :MEM_META_WIN' + winnum + ':$1 0xFFFFFFFF'
  Writetxt2out2(txt)
  txt = 'SHR :MEM_META_WIN' + winnum + ':$3 :MEM_META_WIN' + winnum + ':$1 32'
  Writetxt2out2(txt)
  txt = 'WRW :REG_JX:0x' + toHex(long(segOutA0, 16) + segID*long('10', 16)) + ' :MEM_META_WIN' + winnum + ':$2'
  Writetxt2out2(txt)
  txt = 'WRW :REG_JX:0x' + toHex(long(segOutA1, 16) + segID*long('10', 16)) + ' :MEM_META_WIN' + winnum + ':$3'
  Writetxt2out2(txt)

  #
  # Program test bench registers for this window
  # Code here also needs to read back the TB addresses for the segment and set [start|end][32|64]
  #
  winaddr = WinStart
  txt = '\n-- Program test bench registers for Window ' + segnum
  Writetxt2out2(txt)
  # Setup the WIN register based on the segment MMU register settings
  txt = 'ADD :MEM_META_WIN' + winnum + ':$4 :MEM_META_WIN' + winnum + ':$1 0x00FFFFFF'
  Writetxt2out2(txt)
  # Setup the WIN register based on the segment MMU register settings
  txt = 'AND :MEM_META_WIN' + winnum + ':$5 :MEM_META_WIN' + winnum + ':$4 0xFFFFFFFF'
  Writetxt2out2(txt)
  txt = 'SHR :MEM_META_WIN' + winnum + ':$6 :MEM_META_WIN' + winnum + ':$4 32'
  Writetxt2out2(txt)
  winaddr = '0x' + toHex(long(winaddr, 16) + segID*long('40', 16))
  # Value we need to read from the csim and put in start32[i]
  txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$2'
  Writetxt2out2(txt)
  winaddr = '0x' + toHex(long(winaddr, 16) + long('10', 16))
  # Value we need to read from the csim and put in start64[i]
  txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$3'
  Writetxt2out2(txt)
  winaddr = '0x' + toHex(long(winaddr, 16) + long('10', 16))
  # Value we need to read from the csim and put in end32[i]
  txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$5'
  Writetxt2out2(txt)
  winaddr = '0x' + toHex(long(winaddr, 16) + long('10', 16))
  # Value we need to read from the csim and put in end64[i]
  txt = 'WRW :REG_META_TB:' + winaddr + ' :MEM_META_WIN' + winnum + ':$6'
  Writetxt2out2(txt)

  txt = ''
  Writetxt2out2(txt)

  return


###################################################
# Sets up the testbench to allow register access and print strings
# EnablePrinting
# TODO uses fixed location, should be extended to use argument
###################################################
def SegEnablePrinting() :

  Writetxt2out2('\n-- Enable active windows')
  Writetxt2out2('RDW :MEM_REG_META_TB:$10 :REG_META_TB:0x00002000')
  Writetxt2out2('OR :MEM_REG_META_TB:$10 :MEM_REG_META_TB:$10 0x8000')
  Writetxt2out2('WRW :REG_META_TB:0x00002000 :MEM_REG_META_TB:$10')

  Writetxt2out2('\n-- enable window 15, allow all of register region (linear 0x02000000-0x02FFFFFF)')
  Writetxt2out2('WRW :REG_META_TB:0x00002310 0x00000000')
  Writetxt2out2('WRW :REG_META_TB:0x00002320 0x00010000')
  Writetxt2out2('WRW :REG_META_TB:0x00002330 0x00FFFFFF')
  Writetxt2out2('WRW :REG_META_TB:0x00002340 0x00010000')

  Writetxt2out2('\n-- enable string printing (must occur after segment setup)')
  Writetxt2out2('WRW :REG_JX:0x027FFFF4 0xFEED9011')
  Writetxt2out2('WRW :REG_META_TB:0x00003000 0x00000001')
  Writetxt2out2('WRW :REG_META_TB:0x00003010 0x007FFFF0')
  Writetxt2out2('WRW :REG_META_TB:0x00003020 0x00010000\n')
  
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
  Writetxt2out2(txt)

  txt = '--   Purge thread 0 local and global partitions'
  Writetxt2out2(txt)
  txt = 'WRW :REG_JX:0x04830050 0x00000018'
  Writetxt2out2(txt)
  Target.MemWrite(":REGMETA:" + "0x04830050", "0x00000018");

  txt = '\n--   Purge thread 1 local partition'
  Writetxt2out2(txt)
  txt = 'WRW :REG_JX:0x04830058 0x00000010'
  Writetxt2out2(txt)
  Target.MemWrite(":REGMETA:" + "0x04830058", "0x00000010");

  txt = '\n--   Purge thread 2 local partition'
  Writetxt2out2(txt)
  txt = 'WRW :REG_JX:0x04830060 0x00000010'
  Writetxt2out2(txt)
  Target.MemWrite(":REGMETA:" + "0x04830060", "0x00000010");

  txt = '\n--   Purge thread 3 local partition'
  Writetxt2out2(txt)
  txt = 'WRW :REG_JX:0x04830068 0x00000010'
  Writetxt2out2(txt)
  Target.MemWrite(":REGMETA:" + "0x04830068", "0x00000010")

  txt = '\n--   Poll for flushes to complete'
  Writetxt2out2(txt)
  txt = 'POL :REG_JX:0x04830048 0 0xFFFFFFFF 0 50 200'
  Writetxt2out2(txt)
  Target.MemPol(":REGMETA:" + "0x04830048", "0x00000000", "0x00000001", 0, 1);

###################################################
# Flush the data cache given it's size in bytes
# DCacheFlush <size> 
###################################################
def DCacheFlush(size, out2) :
  if out2 != 0 :
    txt = '\n-- Flush Data Cache: Size 0x' + toHex(size) + ' bytes'
    Writetxt2out2(txt)

  # base = LINSYSCFLUSH_DCACHE_LINE
  base = 0x04400000
  offset = 0

  while (offset < size) :
    addr = '0x' + toHex(base + offset)

    if out2 != 0 :
      txt = 'WRW :REG_JX:' + addr + ' 0x00000000'
      Writetxt2out2(txt)

    Target.MemWrite(":REGMETA:" + addr, '0x00000000')
    offset += 64

###################################################
# Dump the seg mmu mapped memory
# SegMMUMemDump <threadstate:(0-strt/1-end)> 
###################################################
def SegMMUMemDump(thrdst) :
  global Progress

  # Check the state of threads
  if thrdst == 0 :
    # The following functions have been added to diagnose write-back data cache
    # skew issues. Uncomment as necessary.
    # DCachePurge()
    # DCacheFlush(4096)

      for i in range(0, maxSegs) :

      # Check if the segment is configured
       if segLen[i] != 0 :

        if i < 10 :
          winnum = '0' + str(i)
        else :
          winnum = str(i)

        #
        # Dump the contents of physical memory corresponding to the configured segment
        # TO DO: currently assumes a 1:1 match between allocated memory and the linear address
        #         so we are not concerned that [start|end][32|64] are not defined
        #
        fname = 'memseg-st' + str(i) + '.bin'
        if Progress == 1:
          txt = 'Minibench: dumping initial image, segment ' + str(i) + ': base 0x' + toHex(long(start32[i], 16)) + '; length 0x' + toHex(long(segLen[i], 16)) + '.'
          print txt
        MemDump(start32[i], segLen[i], fname)
        txt = '\n-- Load initial image for segment ' + str(i)
        Writetxt2out2(txt)
        txt = 'LDB :MEM_META_WIN' + winnum + ':Seg' + winnum + 'Adr:0x0 ' + segLen[i] + ' 0x00000000 ' + fname + '\n'
        Writetxt2out2(txt)

#      else :
#        winaddr = '0x' + toHex(long(winaddr, 16) + long('40', 16))

  # Check the state of threads - if end state
  elif thrdst == 1 :
    # DCachePurge()

    txt = '\n-- Check end state Memory image for all segments'
    Writetxt2out2(txt)

    for i in range(0, maxSegs) :

      # Check if the segment is configured
      if segLen[i] != 0 :

        if i < 10 :
          winnum = '0' + str(i)
        else :
          winnum = str(i)

        #
        # Dump the contents of physical memory corresponding to the configured segment
        # TO DO: currently assumes a 1:1 match between allocated memory and the linear address
        #         so we are not concerned that [start|end][32|64] are not defined
        #
        fname = 'memseg-end' + str(i) + '.bin'
        if Progress == 1:
          txt = 'Minibench: dumping final image, segment ' + str(i) + ': base 0x' + toHex(long(start32[i], 16)) + '; length 0x' + toHex(long(segLen[i], 16)) + '.'
          print txt
        MemDump(start32[i], segLen[i], fname)

        txt = '\n-- Compare final image for segment ' + str(i)
        Writetxt2out2(txt)
        txt = 'SAB :MEM_META_WIN' + winnum + ':Seg' + winnum + 'Adr:0x0 ' + segLen[i] + ' 0x00000000 ' + fname + '\n'
        Writetxt2out2(txt)

  return

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
  
 
#if __name__ == "__main__" :
#  Target = sys.argv[1]
#  Progress = sys.argv[2]
#  if SetupOut2txt == 1:
#    fout2 = open('tmpregs2out2.txt', 'w')
#    fout2.write('\n')
#    fout2.close()


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

def SetupMb(targ, progrep, mtx=0) :
  
  global Target
  global Progress
  global Mtx
  global TxrxdtAddr
  global TxrxrqAddr
      
  # Target on which the test runs
  Target = targ

  # Flag whether target is MTX or not  
  Mtx = mtx

  # Setup tmpregs2out2.txt to log the registers to be written to out2.txt
  fout2 = open('tmpregs2out2.txt', 'w')
  fout2.write('\n')
  fout2.close()

  # Variable to report progress to the console
  Progress = progrep
  
  if Target == 'FPGA' :
    import FPGA
  elif Target == 'CSim' :
    import CSim

  if Mtx != 0:
    TxrxdtAddr = '000000F8'
    TxrxrqAddr = '000000FC'

  return
     

# End of Minibench.py
