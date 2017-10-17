#*****************************************************************************
#
#               file : $RCSfile: FPGA.py,v $
#             author : $Author: rst $
#  date last revised : $Date: 2010/11/17 14:42:47 $
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
from CSUtils import DAtiny
import time
import re
from re import *

SCRIPT_ADDR_MAP_CHAR = ':'

MetaUxRxDtAddr = int("0x0480FFF0", 16)
MetaUxRxRqAddr = int("0x0480FFF8",16)


###################################################
# Extract offset information from address string
###################################################
def getAddress(address):
  memType = 0
  address = address.strip()
  if  address[0] == SCRIPT_ADDR_MAP_CHAR :
    address = address.strip(SCRIPT_ADDR_MAP_CHAR)
  tmpnum = address.find(SCRIPT_ADDR_MAP_CHAR)
  if tmpnum != -1 :
    offset = address[0:tmpnum]
    address = address[tmpnum+1:]
    address = int(address, 16)
    if offset.upper() == "REGMETA" :
      return address
    elif offset.upper() == "UXRXDTMETA" :
      address = address + MetaUxRxDtAddr
      return address
    elif offset.upper() == "UXRXRQMETA" :
      address = address + MetaUxRxRqAddr
      return address

  else :
    address = int(address, 16)
    return address
    

###################################################
# Read 32bit word but if fail occurs try again
###################################################
def readLongSafe(addr) :
  done = 0
  count = 0
  while done == 0 and count < 3 :
    try:
      res = DAtiny.ReadMemory(addr, 4, 1)
      prog = re.compile(r"^[0-9\-]+$")
      if prog.match(str(res)):
        done = 1
      else :
        count = count + 1
        msg = "ERROR : Read error at " + hexaddr + " " + res
        print msg
    except DA.Error, e:
      err_msg = "ERROR : Failed to read 0x%x address from memory" %(addr)
      print err_msg
      count = count + 1
    
  if done == 0:
    errmsg = "ERROR : Failed to read 0x%x %d times" %(addr,count)
    print errmsg

  return res


###################################################
# Write DWORD to address
# MemWrite :<offset>:<address> <data>
###################################################    
def MemWrite(dest, data) :
  data = int(data,16)
  addr = getAddress(dest)
  
  DAtiny.WriteMemory(addr, data, 4, 1)
   
  return


###############################################################
# Write block to address
# WriteMemoryBlock <address> <dataCount> <ElememtType> <data> <MemoryType>
################################################################    
def WriteMemoryBlock(addr, dataCount, ElememtType, data, MemoryType=1) :
    
  DAtiny.WriteMemoryBlock(addr, dataCount, ElememtType, data, MemoryType)
   
  return


###################################################
# Read DWORD from address
# MemRead :<offset>:<address>
###################################################    
def MemRead(dest) :

  addr = getAddress(dest)
  data = DAtiny.ReadMemory(addr, 4, 1)

  return data

###################################################
# Poll memory location
# MemPol :<offset>:<address> <value> <mask> <time>
###################################################
def MemPol(dest, value, mask="FFFFFFFF", operator=0, ntime=int("0FFFFFFF", 16)) :
  
  if mask == "FFFFFFFF" :
    mask = value
      
  value = int(value, 16)
  mask = int(mask, 16)
  
  value = value & mask
    
  # Argh! if top bit is set get interpreded as negative
  ntime = ntime & 0x0FFFFFFF
    
  # If timeout is set to 0 then it means forever
  if ntime == 0 :
    ntime = int("0FFFFFFF", 16)
    
  addr = getAddress(dest)
    
  tmpmsg = "Poll 0x%08X for 0x%08X : mask 0x%08X : time 0x%08X : operator %d" %(addr, value, mask, ntime, operator)

  passflag = 0
  doneonce = 0
  start = time.time()
    
  while ((time.time() - start)*1000) <= ntime or doneonce == 0:
    data = readLongSafe(addr)
    if (data & mask) == value :
      passflag = 1
      break
    doneonce = 1
      
  if passflag == 1 :
    tmpmsg = "Poll at address 0x%08X PASSED (0x%08X)" %(addr, value)
    # print tmpmsg
  else :
    tmpmsg = "ERROR : Poll at address 0x%08X FAILED (expected = 0x%08X | actual = 0x%08X)" %(address, value, data)
    print tmpmsg
    sys.exit(1)

  return    

###################################################
# Print comment
# COM <Comment>
###################################################    
def Com(strLine) :
  print strLine
  return


###################################################
# Read bytes and append to file
# SAB <filename> <offset>:<address> <length in bytes> <elementsize> <memorytype>
###################################################
def SAB(fname, dest, len, esize=4, memtype=1):
  addr = getAddress(dest)
  DAtiny.SaveBinaryFile(fname, addr, len, esize, memtype)
  return


###################################################
# RWR
# RWR :<offset>:<address> <mask> <data> 
###################################################
def RWR(addr, mask, data) :
  print "Needs Implementation"
  

###################################################
# MRD
# MRD :<offset>:<address> 
###################################################
def MRD(addr) :
  print "Needs Implementation"  
  
  
###################################################
# USR
# USR <value1> <value2> <value3> <value4> 
###################################################
def USR(value1, value2, value3, value4) :
  print "Needs Implementation" 
  
 
###############################################################
# UseTarget
# UseTarget <TargetIdentifier>
################################################################    
def UseTarget(Identifier) :
    
  DAtiny.UseTarget(Identifier)
   
  return


###############################################################
# ResetTarget
# ResetTarget <Halt>
################################################################    
def ResetTarget(halt=0) :

  DAtiny.Reset(halt)

  return


###########################################################################
# LoadFile
# LoadFile <Filename> <Address> <Length in bytes> <ElementSize=4> <MemoryType=1>
###########################################################################    
def LoadFile(fname, addr, len, size=4, memtype=1) :
  
  addr = int(addr, 16)
  len = int(len, 16)
  DAtiny.LoadBinaryFile(fname, addr, len, size, memtype)  
   
  return
 

###################################################
# Test memory location
# MemCheck :<offset>:<address> <value>
###################################################
def MemCheck(dest, value) :
   
  address = getAddress(dest)
  value = int(value, 16)
    
  if address == - 1 :
    return
    
  passflag = 0
  data = readLongSafe(address)
   
  if data == value :
    tmpstr = "MemCheck at address 0x%08X PASSED (0x%08X)" %(address, value)
    # print tmpstr
  else :
    tmpstr = "ERROR : MemCheck at address 0x%08X FAILED (expected = 0x%08X | actual = 0x%08X)" %(address, value, data)
    print tmpstr
    sys.exit(1)
      
  return
    

###############################################################
# InitTarget
# InitTarget <TargetIdentifier> <FPGAType>
################################################################    
def InitTarget(TIdent, FType) :
  
  UseTarget(TIdent)
  ResetTarget()
  ClearFPGAMem(FType)
  
  return
  
  
###############################################################
# ClearFPGAMem
# ClearFPGAMem <FPGAType>
################################################################    
def ClearFPGAMem(ftype) :

  print '\n TestProgress: -- ClearFpgaMemory'
  
  if ftype == "TCF" or ftype == "tcf" :
    filename = "utils/mclear_tcf.bin"
  else :
    filename = "utils/mclear.bin"

  #"SDRAM process" 
  MemWrite("80020000", "00000000")
  dataread = MemRead("80020000")
  
  #"Setting Meson wrapper divider register to 2MHz instead of default 27Mhz"
  MemWrite("03000040", "00000001")
  
  LoadFile(filename, "0x80020000", "0x1200")
  
  #"Starting Thread 0"
  MemWrite("0x04800010", "0x00020000")
  
  MemWrite("0x0480fff0", "0x80020000")
  
  MemWrite("0x0480fff8", "0x00000005")
  
  MemPol("0x0480fff8", "0x80000000")
  
  MemWrite("0x04800000", "0x00000001")
  
  #"Waiting for Thread 0 to finish"
  MemPol("0x80020004", "0x80000000")
  
  MemCheck("0x80020004", "0xababbaba")
  
  #"Acknowledging bits in HWSTATMETA"
  LoadFile(filename, "0x80020000", "0x1200")
 
  #"Starting Thread 1"
  MemWrite("0x04801010", "0x00000000")
  
  MemWrite("0x0480fff0", "0x80020000")
  
  MemWrite("0x0480fff8", "0x00001005")
  
  MemPol("0x0480fff8", "0x80000000")
  
  MemWrite("0x04801000", "0x00000001")
  
  #"Waiting for Thread 1 to finish"
  MemPol("0x80020004", "0x80000000")
  
  MemCheck("0x80020004", "0xababbaba")
  
  #"Acknowledging bits in HWSTATMETA"
  mem_data = [0] * int("0x00001400", 16)
  WriteMemoryBlock(int("0x80020000", 16), int("0x00001400", 16), 4, mem_data) 
 
  mem_data = [0] * int("0x00001200", 16)
  WriteMemoryBlock(int("0xB0000000", 16), int("0x00001200", 16), 4, mem_data)
  
  LoadFile("utils/coredataclear.bin", "0x82000000", "0xFFFFFFFF")
  
  #"Flushing MMCU TLB cache"
  MemWrite("0x04700000", "0x00000000")
  
  #"Complete preparation for test run"
  
  return
  
  
###############################################################
# stopTarget
# stopTarget
################################################################    
def stopTarget() :

  DAtiny.Disconnect()
   
  return


###############################################################
# runFPGA
# runFPGA <TargetIdentifier> <FPGAType>
################################################################    
#def runFPGA(TargetIdent, FPGAType) :
#
#  InitTarget(TargetIdent, FPGAType)
#  
#  #run FPGA test through ldrout.py
#  
#  import ldrout
#  
#  ldrout
#  
#  stopTarget()
  
#  print "done done done"
#  
#  return



if __name__ == "__main__" :
  runFPGA(sys.argv[1], sys.argv[2])  


# End of FPGA.py
