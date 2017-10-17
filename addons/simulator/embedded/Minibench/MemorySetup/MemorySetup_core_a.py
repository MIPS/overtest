#*****************************************************************************
#
#               file : $RCSfile: MemorySetup_core_a.py,v $
#             author : $Author: ral $
#  date last revised : $Date: 2012/10/24 11:14:11 $
#    current version : $Revision: 1.3 $
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
#                      Alternate core memories layout:
#                      core_code  0x80880000 (64KB)
#                      core_data  0x82000000 (64KB)
#
#****************************************************************************


###################################################
# Setup address base and length for minibench library tests
# SetupMemory <library module>
###################################################
def SetupMemory(libmodule) :
  """
  SetupMemory

  Creates a 64K block of core code memory, 64-bit wide access.
  Creates a 64K block of core data memory, 64-bit wide access.
  """

  # Create core code memory
  (pUser, pCallback) = libmodule.ExtMemCreate('0x00010000', '64')

  # Ensure Out2 allocates the core code memory
  libmodule.Out2MemSetup(1, '0x80880000', '0x00010000')

  # Register core code memory
  libmodule.CoreMemRegister(1, '0x80880000', '0x00010000', '64', pUser, pCallback)

  # Create core data memory
  (pUser, pCallback) = libmodule.ExtMemCreate('0x00010000', '64')

  # Ensure Out2 allocates the core data memory
  libmodule.Out2MemSetup(2, '0x82000000', '0x00010000')

  # Register core data memory
  libmodule.CoreMemRegister(2, '0x82000000', '0x000010000', '64', pUser, pCallback)

  return


###################################################
# Dump in-use memory for minibench library tests
# MemDump <library module> <thrdstate-(0-strt/1-end)>
###################################################
def MemDump(libmodule, thrdstate) :

  libmodule.Out2Memdump(1, '0x80880000', '0x00010000', thrdstate)
  libmodule.Out2Memdump(2, '0x82000000', '0x00010000', thrdstate)

  return


# end of MemorySetup_core_a.py

