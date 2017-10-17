#*****************************************************************************
#
#               file : $RCSfile: CSimCmdvars.py,v $
#             author : $Author: saw $
#  date last revised : $Date: 2011/09/01 16:45:36 $
#    current version : $Revision: 1.8 $
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

#Set TXTACTCYC address
TXTACTCYC = int("0x048000F0", 16)
CTThreadOffset = int("0x1000", 16)

# Set of variables required to process Command line arguments
  
CMD_REGDEF_DEFAULT = "./regs.def"
CMD_IGNORE_DEFAULT = "./ignorefile"
CMD_PARAMS_DEFAULT = "./"
CMD_BMPDIR_DEFAULT = "."
CMD_WRAP_DEFAULT = "wrap"
CMD_INFILE_DEFAULT = "out"
CMD_OUTFILE_DEFAULT = "out"
CMD_CADI_INPUT_DEFAULT = "cadi_in.txt"
CMD_LINESTORE_WIDTH = 10
SIM_PATH_MAX = 255

cmdline_RegisterDefaultsFile = CMD_REGDEF_DEFAULT
cmdline_IgnoreFile = CMD_IGNORE_DEFAULT
cmdline_ParamsDir = CMD_PARAMS_DEFAULT
cmdline_BmpDir = CMD_BMPDIR_DEFAULT
cmdline_WrapFile = CMD_WRAP_DEFAULT
cmdline_OutFile = CMD_OUTFILE_DEFAULT
cmdline_CadiInput = CMD_CADI_INPUT_DEFAULT
cmdline_InputFile = CMD_INFILE_DEFAULT
cmdline_InputDirectory =  "."

# Default event synchronisation file name
CMD_SYNCFILE_DEFAULT = "intlog"
cmdline_SyncFile = CMD_SYNCFILE_DEFAULT
cmdline_SyncFileDirectory =  "."


uLinestoreWidth	= CMD_LINESTORE_WIDTH
bHighDefinition	= False
bTiffOutput = False
bSharpIP = False
bInSimTest = False
bForceInSimLog = False
bTransactionMode = False
bQuiet = False
bMTX = False
nRC = 0
uRCode = 0
bRC = False
numOfCores = 1

fpFPGAFile = None
psRegressionOutfiles = None
metacPtr = None

MEMORY_TYPE_UNKNOWN = int("0x00000000", 16)
MEMORY_TYPE_FB = int("0x00000001", 16)
MEMORY_TYPE_REG = int("0x00000002", 16)
MEMORY_TYPE_SLAVE = int("0x00000003", 16)
MEMORY_TYPE_PCI_CFG = int("0x00000004", 16)
SCRIPT_LINE_LEN = 1024
SCRIPT_TOKEN_LEN = 256

SCRIPT_ILIST_END = "iend"
SCRIPT_EXPAND_CHAR = '%'
SCRIPT_ADDR_MAP_CHAR = ':'

SCRIPT_OPTYPE_ADDR = 0
SCRIPT_OPTYPE_VAL = 1
SCRIPT_OPTYPE_CONF = 2
SCRIPT_OPTYPE_FILENAME = 3

SCRIPT_NUM_STREAM_NAMES = 16
MetaUxRxDtAddr = int("0x0480FFF0", 16)
MetaUxRxRqAddr = int("0x0480FFF8",16)

TestTimeOutSecs = 0

if 'METAT_ONETEST_TIMEOUT' in os.environ :
  try:
    TestTimeOutSecs = int(os.environ['METAT_ONETEST_TIMEOUT'])
  except ValueError:
    None # Ignore bad timeout values
  
if TestTimeOutSecs <= 0 :
  TestTimeOutSecs = 10 * 60


# End of CSimCmdvars.py
