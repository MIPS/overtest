################################################################################
#
#               file : $RCSfile: CSim.py,v $
#             author : $Author: anb $
#  date last revised : $Date: 2012/12/14 16:41:08 $
#    current version : $Revision: 1.1 $
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
################################################################################

import sys
import os
import time
from time import localtime, strftime
import atexit
import platform

import struct
from re import search

import CSimCmdvars

# Variable to hold the imported module _mbsimapi
CSimapi = None

# max number of threads
maxthreads = 4

# Debug varible to count how many events we have posted
evtCount = 0

# Global cycle array which used to store the 
# start cycle of each thread, since vhdl will only
# start logging, so we need to add the cycles to the cycles read from the log
startCycle = [0]*maxthreads

###################################################
# Extract offset information from address string
###################################################
def getAddress(address):
  memType = 0
  address = address.strip()
  if  address[0] == CSimCmdvars.SCRIPT_ADDR_MAP_CHAR :
    address = address.strip(CSimCmdvars.SCRIPT_ADDR_MAP_CHAR)
  tmpnum = address.find(CSimCmdvars.SCRIPT_ADDR_MAP_CHAR)
  if tmpnum != -1 :
    offset = address[0:tmpnum]
    address = address[tmpnum+1:]
    address = int(address, 16)
    if offset.upper() == "REGMETA" :
      memType = CSimCmdvars.MEMORY_TYPE_REG
      return (memType, address)
    elif offset.upper() == "UXRXDTMETA" :
      memType = CSimCmdvars.MEMORY_TYPE_REG
      address = address + CSimCmdvars.MetaUxRxDtAddr
      return (memType, address)
    elif offset.upper() == "UXRXRQMETA" :
      memType = CSimCmdvars.MEMORY_TYPE_REG
      address = address + CSimCmdvars.MetaUxRxRqAddr
      return (memType, address)
    elif offset.upper() == "REG_MTX" :
      memType = CSimCmdvars.MEMORY_TYPE_REG
      ##### Should get back ####
      if CSimCmdvars.bMTX == True :
        address = address + int("0x04800000", 16)
      return (memType, address)
    elif offset.upper() == "REGMTXCODE" :
      memType = CSimCmdvars.MEMORY_TYPE_FB
      address = address + int("0x80880000", 16)
      return (memType, address)
    elif offset.upper() == "REGMTXDATA" :
      memType = CSimCmdvars.MEMORY_TYPE_FB
      address = address + int("0x82880000", 16)
      return (memType, address)
    elif offset.upper() == "REGSIMCODE" :
      memType = CSimCmdvars.MEMORY_TYPE_PCI_CFG
      address = address + int("0x80900000", 16)
      return (memType, address)
    elif offset.upper() == "REG_SLVDBG" :
      memType = CSimCmdvars.MEMORY_TYPE_SLAVE
      return (memType, address)
    else :
      memType = CSimCmdvars.MEMORY_TYPE_PCI_CFG
      return (memType, address)
  else :
    address = int(address, 16)
    memType = CSimCmdvars.MEMORY_TYPE_FB
    return (memType, address)

###################################################
# Write DWORD to address
# MemWrite :<offset>:<address> <data>
###################################################
def MemWrite(dest, data) :
  data = int(data,16)
  mem, addr = getAddress(dest)

  CSimapi.MBSIM_MemoryWriteDWORD(CSimCmdvars.metacPtr, addr, mem, data)

  return

###################################################
# Read DWORD from address
# MemRead :<offset>:<address>
###################################################
def MemRead(dest) :
  mem, addr = getAddress(dest)
  data = CSimapi.MBSIM_MemoryReadDWORD(CSimCmdvars.metacPtr, addr, mem)

  return data

###################################################
# Poll memory location
# MemPol :<offset>:<address> <value> <mask> <time>
###################################################
def MemPol(dest, value, mask="FFFFFFFF", operator=0, ntimes=1) :
  interval = 0

  value = int(value, 16)
  mask = int(mask, 16)

  mem, addr = getAddress(dest)

#  tmpmsg = "Poll 0x%02X:0x%08X for 0x%08X: mask = 0x%08X; operator %d; times %d" %(mem, addr, value, mask, operator, ntimes)
#  print tmpmsg

  CSimapi.MBSIM_RegisterPoll(CSimCmdvars.metacPtr, CSimCmdvars.TestTimeOutSecs, addr, mem, value, mask, operator, ntimes, interval)

  return

###################################################
# Print comment
# COM <Comment>
###################################################
def Com(strLine) :
  CSimapi.MBSIM_PrintCOM(CSimCmdvars.metacPtr, strLine)
  CSimapi.MBSIM_PrintCOM(CSimCmdvars.metacPtr, '\n')
  return

###################################################
# Read bytes and append to file
# SAB <filename> <offset>:<address> <length in bytes> <elementsize> <memorytype>
###################################################
def SAB(fname, dest, len, esize=4, memtype=1):
  BufSize = 65536
  fout = open(fname, 'ab')

  Buf = CSimapi.malloc_ByteBuf(BufSize)

  mem, addr = getAddress(dest)
  FromAddr = addr
  ToAddr = addr + len

  while FromAddr < ToAddr :
    NumRead = CSimapi.MBSIM_PhysMemRead(CSimCmdvars.metacPtr, FromAddr, BufSize, Buf)
    NewData = CSimapi.cdata_ByteBuf(Buf, NumRead)

    # Bail out if CSim read is empty
    if ( NumRead == 0 ) :
      print "CSim.SAB warning: Read of 0x%08x bytes at 0x%08x returned none." %(BufSize, FromAddr)
      break

    fout.write(NewData[0:NumRead])
    FromAddr = FromAddr + NumRead

  CSimapi.free_ByteBuf(Buf)

  fout.close()

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

################################################################
# Write DWORD block to address
# WriteMemoryBlock <address> <length of block> <datatype> <dataSequence>
################################################################
def WriteMemoryBlock(dest, len, datatype, dataSequence, MemoryType=CSimCmdvars.MEMORY_TYPE_FB) :
  i = 0

  for data in dataSequence :
    CSimapi.MBSIM_MemoryWriteDWORD(CSimCmdvars.metacPtr, dest, MemoryType, data)
    dest = dest + 4
    i = i + 1

  return i

################################################################
# Process the commandline args
# 
################################################################
def cmdline_Process(options):
  for (o,a) in options:
    # Specifies an alternate register defs file.
    if o == "--regdef" :
      CSimCmdvars.cmdline_RegisterDefaultsFile = a

    # Specifies an alternate ignore file.
    elif o == "--ignorefile" :
      CSimCmdvars.cmdline_IgnoreFile = a

    # Specifies an alternate params directory.
    elif o == "--paramdir" :
      CSimCmdvars.cmdline_ParamsDir = a

    # Specifies an alternate filename for the out.bmp file.
    elif o == "--fo" :
      CSimCmdvars.cmdline_OutFile = a

    # Specifies use of tiff output image.
    elif o == "--tiff" :
      CSimCmdvars.bTiffOutput = True

    # Specifies use of SharpIP image.
    elif o == "--sharpip" :
      CSimCmdvars.bSharpIP = True

    # Specifies an alternate directory for the out.bmp file.
    elif o == "--bmpdir" :
      CSimCmdvars.cmdline_BmpDir = a

    # Specifies an alternative wrapper file.
    elif o == "--fw" :
      CSimCmdvars.cmdline_WrapFile = a

    # Specifies an alternative input file.
    elif o == "--fi" :
      CSimCmdvars.cmdline_InputFile = a
      CSimCmdvars.cmdline_InputDirectory = os.path.dirname(os.path.abspath(a))

    # Specifies an alternative imput file for the cadi.
    elif o == "--fcadi" :
      CSimCmdvars.cmdline_CadiInput = a

    # Specifies an alternative line store width.
    elif o == "--linestorewidth" :
      CSimCmdvars.uLinestoreWidth = int(a)

    # Specifies high definition YUV to RGB conversion matrix.
    elif o == "--highdef" :
      CSimCmdvars.bHighDefinition = True

    elif o == "--regressoutfile" :
      CSimCmdvars.psRegressionOutfiles = a

    elif o == "--insimtest" :
      CSimCmdvars.bInSimTest = True

    elif o == "--rc" :
      CSimCmdvars.bRC = True
      CSimCmdvars.nRC = 0
      CSimCmdvars.uRCode = 0
      colonfind = a.find(':')
      if colonfind != -1 :
        CSimCmdvars.nRC = int(a[:colonfind])
        CSimCmdvars.uRCode = int(a[(colonfind+1):], 16)
      else :
        CSimCmdvars.nRC = int(a)

    elif o == "--forceinsimlog" :
      CSimCmdvars.bForceInSimLog = True

    # Enable transaction modelling
    elif o == "--transaction" :
      CSimCmdvars.bTransactionMode = True

    # Specifies the event synchronisation file name.
    elif o == "--timing" :
      CSimCmdvars.cmdline_SyncFile = a
      CSimCmdvars.cmdline_SyncFileDirectory = os.path.dirname(os.path.abspath(a))

    elif o == "--quiet" :
      CSimCmdvars.bQuiet = True

    elif o == "--mcs" :
      CSimCmdvars.numOfCores = int(a)

    elif o == "--mtx" :
      CSimCmdvars.bMTX = True;

    elif o in ("--help" or "-h") :
      print "PMX2 Simulator. \n\nCommand line options:"
      print "\n  --regdef filename \tRead register defaults from filename.\n\t\t\tDefault file is %s" %CSimCmdvars.CMD_REGDEF_DEFAULT
      print "\n  --ignorefile filename\tRead HIDebug ignore settings from filename.\n\t\t\tDefault file is %s" %CSimCmdvars.CMD_IGNORE_DEFAULT
      print "\n  --paramdir filename \tDirectory to write output files in.\n\t\t\tDefault directory is %s" %CSimCmdvars.CMD_PARAMS_DEFAULT
      print "\n  --bmpdir filename \tDirectory to write bitmap file in.\n\t\t\tDefault directory is %s" %CSimCmdvars.CMD_BMPDIR_DEFAULT
      print "\n  --objanal filename \tlocation of objanal executable.\n\t\t\tDefault exe is %s (PC only)" %"????"
      print "\n  --fo filename     \tfilname of bitmap file written out.\n\t\t\tDefault filename is %s" %CSimCmdvars.CMD_OUTFILE_DEFAULT
      print "\n  --fw filename     \tRead script wrapper from filename.\n\t\t\tDefault file is %s" %CSimCmdvars.CMD_WRAP_DEFAULT
      print "\n  --fi filename     \tRead input files from filename.\n\t\t\tDefault file is %s" %CSimCmdvars.CMD_INFILE_DEFAULT
      print "\n  --insimtest       \tUse inscript as a linux simulator.\n\t\t\tDefault is off"
      print "\n  --linestorewidth width   \tNumber of bits in scaler/i2p linestores.\n\t\t\tDefault value is %i" %CSimCmdvars.CMD_LINESTORE_WIDTH
      print "\n  --mtx             \tUse MTX simulator.\n\t\t\tDefault is META"
      print "\n  --quiet           \tRemove simulator and inscript stdout chatter"
      print "\n  --forceinsimlog   \tForce to log insim.log.\n\t\t\tyou have to got insimlog that contain insim.log in the same directory"
      print "\n  --transaction     \tTurn on transaction mode.\n\t\t\tDefault is normal mode"
      print "\n  --rc num[:code]   \tThread exits needed[:code in hex]\n\t\t\tDefault num is 0 for all and code is 0\n"
      print "\n  --timing filename \tSynchronisation file from filename.\n\t\t\tDefault file is %s" %CSimCmdvars.CMD_SYNCFILE_DEFAULT
      print "\n  --mcs num         \tIndicate multiple cores support\n\t\t\tDefault num is 1 we only support one core\n\n\n"

  return

################################################################
# Build a C-array from a list
# build_array <list>
################################################################
def build_array(l):
  nitems = len(l)
  a = CSimapi.new_ularray(nitems)
  for i in range(0, nitems):
    CSimapi.ularray_setitem(a, i, l[i])
  return a

################################################################
# CloseCOMFile()
# 
################################################################
def CloseCOMFile():
  Metacptr = CSimCmdvars.metacPtr
  if Metacptr != None :
  	CSimapi.MBSIM_CloseCOMFile(Metacptr)

################################################################
# InitTarget()
# 
################################################################
def InitMultiTarget( num, cfgfiles ):
  for i in (0, num):
    InitTarget(cfgfiles)

################################################################
# InitTarget()
# 
################################################################
def InitTarget( cfgfilename ):
  # Get a new blank state we can customise 
  TMetacptr = CSimapi.MBSIM_AllocTemplate()
  CSimCmdvars.metacPtr = TMetacptr

  # To see whether we could open the configuration file
  if cfgfilename != None:
    CSimapi.MBSIM_SetupCfgFile(TMetacptr, cfgfilename)
  else:
    # Use default configuration file
    CSimapi.MBSIM_SetupCfgFile(TMetacptr, None)

  # Setup stdout redirection
  if CSimCmdvars.bQuiet :
    try:
      filePtr = CSimapi.MBSIM_FileOpen(".comout", "w+")
      CSimapi.MBSIM_SetupCOMFile(TMetacptr, filePtr)
    except:
      stdErrfPtr = CSimapi.MBSIM_GetSTDERR()
      CSimapi.MBSIM_WriteCOM(stdErrfPtr, "error on fopen comout\n")
      sys.exit(2)
    atexit.register(CloseCOMFile)
  else :
    stdoutPtr = CSimapi.MBSIM_GetSTDOUT()
    CSimapi.MBSIM_SetupCOMFile(TMetacptr, stdoutPtr)

  # Reset in disguise
  Metacptr = CSimapi.MBSIM_InitMetaSim(TMetacptr)
  CSimapi.MBSIM_FreeTemplate(TMetacptr);
  TMetacptr = None;

  # Open so we can close later
  CSimapi.MBSIM_MetaHostIOCTL(Metacptr, CSimapi.MBSIM_METAGIOCTL_OPEN, 0, None, 0, None, None);

  # Configure logging and io system
  params = [0,0]
  params[1] = params[1] | CSimapi.MBSIM_INSIMOPT_MSUBLOG
  params[1] = params[1] | CSimapi.MBSIM_INSIMOPT_NOJTAGLOG
  params[1] = params[1] | CSimapi.MBSIM_INSIMOPT_NOLOCALRIO

  # If force insim.log option selected, we set the bit to force insim logging
  if CSimCmdvars.bForceInSimLog :
    params[1] = params[1] | CSimapi.MBSIM_INSIMOPT_FORCEINSIMLOG

  if CSimCmdvars.bInSimTest :
    # Do not log Host IO as InSimStartEvt/InSimEndEvt logic is in use
    params[1] = params[1] | CSimapi.MBSIM_INSIMOPT_NOHOSTLOG
  else :
    # Do log Host IO and allow logging from reset itself for boot texts
    params[1] = params[1] | CSimapi.MBSIM_INSIMOPT_BOOTLOG

  if CSimCmdvars.bTransactionMode :
    # Run simulator in transaction mode
    params[1] = params[1] | CSimapi.MBSIM_INSIMOPT_TRANSACT

  # Enable static testing option to enable simulator servicing traps on windows
  if platform.system() == "Windows":
    params[1] = params[1] | CSimapi.MBSIM_INSIMOPT_RSRVD0

  params_array = build_array(params)

  CSimapi.MBSIM_MetaHostIOCTL(Metacptr, CSimapi.MBSIM_METAGIOCTL_START, 2, params_array, 0, None, None)

  CSimapi.delete_ularray(params_array)

  return Metacptr

################################################################
# InScriptClose()
# 
################################################################
def InScriptClose(ptrMetac) :
  TimeOut = 20
  params = [0,0]
  params[1] = CSimapi.MBSIM_INSIMOPT_MSUBLOG

  params_array = build_array(params)

  CSimapi.MBSIM_MetaHostIOCTL(ptrMetac, CSimapi.MBSIM_METAGIOCTL_STOP, 2, params_array, 0, None, None)
  CSimapi.MBSIM_MetaHostIOCTL(ptrMetac, CSimapi.MBSIM_METAGIOCTL_CLOSE, 0, None, 0, None, None)

  while ((CSimapi.MBSIM_GetHostIfResValue(ptrMetac) != CSimapi.MBSIM_SIM_DONE) and TimeOut) :
    setValue = CSimapi.MBSIM_ExecMetaSim(ptrMetac, None)
    CSimapi.MBSIM_SetHostIfResValue(ptrMetac, setValue)
    TimeOut = TimeOut - 1

  CSimapi.delete_ularray(params_array)

  return

################################################################
# InitSim()
# 
################################################################
def InitSim(opt):
  # Command line processing, in particular, will change the debug flags.
  cmdline_Process(opt)

  # Check for params directory, create if necessary
  if CSimCmdvars.cmdline_ParamsDir != CSimCmdvars.CMD_PARAMS_DEFAULT and not os.path.exists(CSimCmdvars.cmdline_ParamsDir):
    os.mkdir(CSimCmdvars.cmdline_ParamsDir)

#  FPGAFile = CSimCmdvars.cmdline_InputFile + ".fpga"
#  CSimCmdvars.fpFPGAFile = open(FPGAFile, "w")

################################################################
# FinishSim()
# 
################################################################
def FinishSim() :
  if CSimCmdvars.fpFPGAFile :
    CSimCmdvars.fpFPGAFile.close()
  return

################################################################
# SimStart()
# cfgfilename - is used to specify configuration file name
################################################################
def SimStart(cmdopts, arguments, cfgfilename ):

  global CSimapi
  global extmem

  # Parse the command line
  InitSim(cmdopts)

  keys = os.environ.keys()

  found = 0

  # Check for METAG_FSIM_ROOT in path and import the module _mbsimapi
  for key in keys:
    if search("METAG_FSIM_ROOT", key):
      found = 1
      break

  if found == 0  :
    print '\nSimulator (METAG_FSIM_ROOT) not specified\n'
    sys.exit(2)
  else :
    mb = os.environ['METAG_FSIM_ROOT'] + '/local/lib/'
    sys.path.append(mb)
    if CSimCmdvars.bQuiet == False :
      print '\nSimulator importing shared library from %s' %mb

  # Pick up options we are interested in
  for (o,a) in cmdopts:
    if o == "--mtx" :
      CSimCmdvars.bMTX = True

  if CSimCmdvars.bMTX == True :
    if CSimCmdvars.bQuiet == False :
      print 'Simulator shared library _mbmtxapi'
    import _mbmtxapi
    CSimapi = _mbmtxapi
  else :
    if CSimCmdvars.bQuiet == False :
      print 'Simulator shared library _mbsimapi'
    import _mbsimapi
    CSimapi = _mbsimapi
  import _extmem
  if not CSimCmdvars.bQuiet:
    print 'Simulator shared library _extmem'
  extmem = _extmem

  # Initialise the simulator
  pMETAC = InitTarget( cfgfilename )

  # Read the CT.0 register TXENABLE directly
  Thread = 0
  Value = CSimapi.MBSIM_MetaHostRead(pMETAC, Thread, CSimapi.MBSIM_GetT0UCTREG0Val())

  # Write back the same state
  CSimapi.MBSIM_MetaHostWrite(pMETAC, Thread, CSimapi.MBSIM_GetT0UCTREG0Val(), Value)

  CSimCmdvars.metacPtr = pMETAC

  return pMETAC

################################################################
# SimClose()
# 
################################################################
def SimStop(MetacPntr) :
  rc = 0
  InScriptClose(MetacPntr)
#  FinishSim()

  if CSimCmdvars.bRC :
    tnum = 0
    rc = 0

    if CSimCmdvars.nRC != 0 :
      for tnum in range(0,4) :
        # Count exit codes
        if CSimapi.MBSIM_GetExitVecValue(MetacPntr, tnum) != CSimapi.MBSIM_NO_EXIT_RC :
          # Thread has completed
          CSimCmdvars.nRC = CSimCmdvars.nRC - 1

      if CSimCmdvars.nRC > 0 :
        print "Exit missing from %d threads" %CSimCmdvars.nRC
        rc = 2
      elif CSimCmdvars.nRC < 0 :
        print "Exit received from %d too many threads" %CSimCmdvars.nRC

    tnum = 0
    for tnum in range(0,4) :
      res = CSimapi.MBSIM_GetExitVecValue(MetacPntr, tnum)
      if res != CSimapi.MBSIM_NO_EXIT_RC :
        if CSimCmdvars.nRC < 0:
          print "    exit %d from thread %d" %(res, tnum)
          continue

        if res == int('0x7E57900D', 16) and CSimCmdvars.uRCode == 0 :
          res = 0

        if res != CSimCmdvars.uRCode :
          if rc != 0 :
            if rc != res :
              rc = 2
          else :
            if res == 0 :
              rc = 2
            else:
              rc = res

      elif CSimCmdvars.nRC > 0 :
        print "   no exit from thread %d" %tnum

    if CSimCmdvars.nRC != 0 :
      rc = 2
    else :
      rc = rc

  # Finally close down the simulator instance
  CSimapi.MBSIM_CloseCOMFile(MetacPntr)
  CSimapi.MBSIM_SetupCOMFile(MetacPntr, CSimapi.MBSIM_GetSTDOUT() )
  CSimapi.MBSIM_MetaHostIFClose(MetacPntr)
  CSimCmdvars.metacPtr = None

  return rc  


################################################################
# Execute()
################################################################
def Execute(MetacPntr, cycles) :
  executed = CSimapi.MBSIM_Execute(MetacPntr, cycles)
  return executed

################################################################
# QueryThreadState()
################################################################
def QueryThreadState(MetacPntr, thread) :
  # Valid thread states
  # 0 - Default(state is unknown)
  # 1 - Disabled
  # 2 - Executing
  # 3 - Halted by receiving InSimVarStart
  # 4 - Halted by receiving InSimVarStop
  thrdstate = CSimapi.MBSIM_QueryThreadStatus(MetacPntr, thread)

  return thrdstate

################################################################
# SetTarget(MetacPntr)
################################################################
def SetTarget(MetacPntr) :
  CSimCmdvars.metacPtr = MetacPntr
  return

################################################################
# AckLogEvent()
################################################################
def AckLogEvent(MetacPntr) :
  result = CSimapi.MBSIM_AckLogEvent(MetacPntr)
  return result

################################################################
# PhysMemDeclare(AdrMask, MatchMask, Size, Width, Name)
#			AdrMask:   64 bit mask of valid address bits to which the registered
#									region will respond.
#			MatchVal: Value of 64-bit address to match with.
#			Size:      size in bytes of the block to register.
#			Width:     width of the region, in bits.
#			Name:      name of the region.
################################################################
def PhysMemDeclare(AdrMask, MatchVal, Size, Width, Name) :
  result = CSimapi.MBSIM_PhysMemDeclare (CSimCmdvars.metacPtr, None,          \
                                         long(AdrMask,16), long(MatchVal,16), \
                                         long(Size,16), long(Width,16), Name, \
                                         None)
  return result

############################################################################
# MemPortDeclare(pUser,Port,AdrMask, MatchVal, Size, Width, Name ,pCallback)
#			pUser  :Pointer to user supplied data. This data is supplied
#                             when registering the callback.
#			Port   :Port  Defines the port to be used.
#                         0 System Bus
#                         1 Core Code Memory
#                         2 Core Data Memory				  
#			AdrMask:   64 bit mask of valid address bits to which the 
#						registered	region will respond.
#			MatchVal: Value of 64-bit address to match with.
#			Size:      size in bytes of the block to register.
#			Width:     width of the region, in bits.
#			Name:      name of the region.
################################################################################ 
def MemPortDeclare(pUser,Port,AdrMask, MatchVal, Size, Width, Name ,pCallback) :

  result = CSimapi.MBSIM_MemPortDeclare (CSimCmdvars.metacPtr, 			\
  	pUser,long(Port),long(AdrMask,16), long(MatchVal,16),				\
	long(Size,16), long(Width,10), Name, pCallback)		

  return result
################################################################
# CreateExtMem( Size)
#			Size:      size in bytes of the block to register.
#			Width:     Width of system bus
################################################################ 
def CreateExtMem( Size, Width) :
  result = extmem.MBEXTMEMNew (long(Size,16), long(Width,10))
  return result
  
################################################################
# GetCallback( )
################################################################ 
def GetCallback(pUser) :
  result = extmem.MBEXTMEMGetCallback (pUser)

  return result

#################################################################
# Sets up attribute
# attribute_type (0x23- share core memory option)
# att_set :  buffer large enough to store the attribute requested
# size    :size of buffer
#################################################################
def ATTRSet( Attrib, attr_set, size) :

  att_set1 = CSimapi.new_ImgUint32_p ()
  InfoSize = CSimapi.new_ImgUint32_p ()
  CSimapi.ImgUint32_p_assign (att_set1, attr_set)
  CSimapi.ImgUint32_p_assign (InfoSize, size)

  result = CSimapi.MBSIM_ATTRSet (CSimCmdvars.metacPtr,     \
    long(Attrib,16),att_set1, InfoSize)

  return result

################################################################
# SetExtMemIO(Index, Base, Size)
#			Index:     Specify which memory block should be used 
#			Base:      Base of this memory block
#			Size       Size of this memory block
################################################################
def SetExtMemIO(Index, Base, Size) :

  if not CSimCmdvars.bQuiet:
    print "CSim.SetExtMemIO: %d, 0x%08x, 0x%08x" %(long(Index), long(Base,16), long(Size,16))
  result = CSimapi.MBSIM_SetExtMemIO (CSimCmdvars.metacPtr, long(Index), \
                                      long(Base,16), long(Size,16), None)
  return result

################################################################
#  InitThreadStartCycle (MetacPntr)
#  Set up the start cycle of each thread (start at InSimStartEvt)
#     MetacPntr:     Specify which memory block should be used 
#     Verbose:       Verbose logging option
################################################################
def InitThreadStartCycle (MetacPntr, Verbose) :
  # Set up start Cycle for each thread 
  for thread in range(0, maxthreads) :
    # Calculate thread TXACTCYC address
    ACTCYCAddr = CSimCmdvars.TXTACTCYC+thread*CSimCmdvars.CTThreadOffset
    startCycle[thread] = CSimapi.MBSIM_MemoryReadDWORD(MetacPntr, ACTCYCAddr, CSimCmdvars.MEMORY_TYPE_REG)
    if Verbose == 1 :
      print "start cycle thread %d %d" %(thread, startCycle[thread])

################################################################
#  def SetSyncEvent ( MetacPntr, hEvent, Thread, Cycle, Value )
#  set the cycle and value of the sync event for this thread
#   the event is specified by hEvent
#			metacpntr:     specify which memory block should be used 
#			hEvent:        specify the event
#			Thread:        Thread ID
#			Cycle:         At which TXTACTCYCL we synchronise
#			Value:         specify which event we expected 
################################################################
def SetSyncEvent ( MetacPntr, hEvent, Thread, Cycle, Value ) :
  Result = 0
  if hEvent != 0 :
    # Set the thread synchronisation cycle
    Result = CSimapi.MBSIM_EVENTSetTimeThrdSync( MetacPntr, hEvent, Thread, Cycle )
    if Result == 0 :
      # Set the event value ( tell what type of interrupt we expect)
      Result = CSimapi.MBSIM_EVENTSetCoreValue( MetacPntr, hEvent, Thread, Value )
  return Result

################################################################
#  EventSync (MetacPntr, line)
#     MetacPntr:     Specify which memory block should be used 
#     line:          Event string to be parsed
#     threads:       Specify how many threads we have
#     Verbose:       Verbose logging option
################################################################
def EventSync (MetacPntr, line, threads, Verbose) :
  Result=0
  global evtCount
  import re
  # Igonore the first line of the log file, it is reset
  prog = re.compile(r"RESET")
  if Verbose == 1 :
    print "%s" %(prog.search(line))
  # if length of the line is 0, there is nothing to be processed
  if len(line) == 0 or prog.search(line) is not None :
    print "Not a real event"
    if len(line) == 0 :
      print "Nothing to %d" %(SyncFile is None)
    else :
      print "Reset %s" %line
  else :
    slen = line.split()
    if Verbose == 1 :
      print "line: %s split: %d" %(line, len(slen))

    # Get thread mask to determine the active thread that expects event
    ThrdMask = line.split()[0]
    # thread ID
    Thread = 0

    # Try to handle synchronisation events happen at same clock cycle of different thread
    Cycle = 0
    Value = 0
    realCycle = 0
    # Create a hEvent type pointer to be used
    hEvent = CSimapi.new_hEvent_p()

    # Check whether there is empty slot available, if yes
    # then we register the event with threadmask and type
    Result = CSimapi.MBSIM_EVENTNewSetCore (MetacPntr, CSimapi.e_MBSimCE_StatusInt, int(ThrdMask,16), hEvent)

    if Result == 0 :
      # Get the handle of the current hEvent
      hEventVal= CSimapi.hEventp_value(hEvent)
      TMask = int(ThrdMask,16)
      # Tell the current position of the line, so we can calculate the correct parameter to use
      curPos = 1

      # We need to get synchronisation point for all threads
      while Thread != threads :
        # Get the cycle parameter for this thread
        Cycle = line.split()[curPos]
        # point to the next parameter
        curPos = curPos+1

        # If current thread expect event, then we read the value for this thread
        Value = int(line.split()[curPos],16)
        curPos = curPos+1

        # Calculate the real cycle, we need to add in the active cycle before InSimStartEvt
        realCycle = startCycle[Thread] + int(Cycle, 16)

        if Verbose == 1 :
          print "Cnt: %d hEvent:%d ThrdMask: 0x%x %d 0x%x 0x%x %d" %(evtCount, hEventVal, int(ThrdMask,16), (int(ThrdMask,16)>>Thread) & 1, int(Cycle,16), realCycle, Value)
        # Set the new core event, put this event into the time event queue
        Result=SetSyncEvent (MetacPntr, hEventVal, Thread, realCycle, Value)

        # advance Thread Id
        Thread = Thread+1
        TMask = TMask>>1

      if Result == 0 :
        # Since all goes fine, then we can post the event into the core
        Result = CSimapi.MBSIM_EVENTSend (MetacPntr, hEventVal)

      # When all things go on fine, we count one event
      # Just a debug variable so that we can count how many events we processed
      if Result == 0 :
        evtCount = evtCount + 1

  return Result

################################################################
#  def QueryStatus ( MetacPntr, Status )
#  Query the current status of the simulation.
#   MetacPntr: The Meta Sim to query
################################################################
def QueryStatus ( MetacPntr ) :
  """Query the current status of a META C Sim instance

  Takes pointer to the META C Sim instance to query

  Returns:
  0 - Normal status.
  1 - Pending outgoing EVENTs which should be read and handled
  """

  Status = CSimapi.new_ImgUint64_p ()
  Result = CSimapi.MBSIM_QUERYStatus (MetacPntr, Status)
  return CSimapi.ImgUint64_p_value (Status)

def GetSimVersion ( ) :
  """Get the version of the META C Simulator

  Queries the version of the META C Simulator and returns it as a string
  """

  Major    = CSimapi.new_ImgUint_p ()
  Minor    = CSimapi.new_ImgUint_p ()
  Rev      = CSimapi.new_ImgUint_p ()
  Build    = CSimapi.new_ImgUint_p ()
  InfoSize = CSimapi.new_ImgUint_p ()
  CSimapi.ImgUint_p_assign (InfoSize, 0)

  CSimapi.MBSIM_GetVersion (Major, Minor, Rev, Build, None, InfoSize)

  str = '%d.%d.%d.%d' %(CSimapi.ImgUint_p_value (Major), \
                        CSimapi.ImgUint_p_value (Minor), \
                        CSimapi.ImgUint_p_value (Rev),   \
                        CSimapi.ImgUint_p_value (Build))
  return str

def HandleEvent ( MetacPntr ) :
  hEvent = CSimapi.new_hEvent_p ()
  Type = CSimapi.new_EvtType_p ()
  Result = CSimapi.MBSIM_EVENTReceive (MetacPntr, hEvent, Type)

  SigGrp = CSimapi.new_SigGrp_p ()
  ValidMask = CSimapi.new_ImgUint32_p ()
  State = CSimapi.new_ImgUint32_p ()

  Result = CSimapi.MBSIM_EVENTFreeGetSignals (MetacPntr, CSimapi.hEvent_p_value(hEvent), SigGrp, ValidMask, State)

  SigGrpVal = CSimapi.SigGrp_p_value (SigGrp)
  MaskVal = CSimapi.ImgUint32_p_value (ValidMask)
  StateVal = CSimapi.ImgUint32_p_value (State)

  Msg = 'FreeGetSignals: Res: ' + str (Result)
  Msg += ' SigGrp: ' + str (SigGrpVal)
  Msg += ' Mask: ' + str (hex (MaskVal))
  Msg += ' State: ' + str (hex (StateVal))
  print Msg

  if SigGrpVal == 6 :
    # It's a GPIO Output Signal.

    # Create and immediately feed new Event to feed back to sim...
    Result = CSimapi.MBSIM_EVENTNewSetSignals (MetacPntr, 7, 0xFFFFFFFF, StateVal, None)

# End of CSim.py
