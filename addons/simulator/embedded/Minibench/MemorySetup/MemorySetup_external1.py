#*****************************************************************************
#
#               file : $RCSfile: MemorySetup_external1.py,v $
#             author : $Author: rst $
#  date last revised : $Date: 2012/05/15 15:04:20 $
#    current version : $Revision: 1.1 $
#
#          copyright : 2012 by Imagination Technologies.
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
#        description : Meta MiniBench memory layout script
#                      External memories at 0xB1000000
#
#            defines :
#
#****************************************************************************


###################################################
# Setup address base and length for minibench library tests
# SetupMemory <library module>
###################################################
def SetupMemory(libmodule) :

  # Declare use of external memory
  libmodule.ExtMemDeclare()

  # Allocate external memory
  libmodule.Out2MemSetup(0, '0xB1000000', '0x01000000' )

  return


###################################################
# Dump in-use memory for minibench library tests
# MemDump <library module> <thrdstate-(0-strt/1-end)>
###################################################
def MemDump(libmodule, thrdstate) :

  libmodule.Out2Memdump(0, '0xB1000000', '0x01000000', thrdstate)

  return


# end of MemorySetup_external1.py

