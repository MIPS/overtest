#*****************************************************************************
#
#               file : $RCSfile: FrisaL2.py,v $
#             author : $Author: rst $
#  date last revised : $Date: 2012/04/18 16:25:48 $
#    current version : $Revision: 1.2 $
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
#        description : Meta MiniBench special script for Frisa: use L2 cache
#
#            defines :
#
#****************************************************************************

import os
#import sys
#from sys import path

#import shutil

import Minibench

# No special initialisation needed in preout2
def initOut2 () :
  return


# Set up and enable the L2 cache before the out2 starts the threads running
def Regs2out2start () :
  # Initialise L2 cache and poll for completion
  Minibench.Writetxt2out2 ('\n-- Initialise L2 cache and poll for completion')
  Minibench.Writetxt2out2 ('WRW :REG_JX:0x048300C0 0x00000001')
  Minibench.Writetxt2out2 ('POL :REG_JX:0x048300C0 0x00000001 0x00000001 0 2500 20000')

  # Enable L2 cache
  Minibench.Writetxt2out2 ('\n-- Enable L2 cache')
  Minibench.Writetxt2out2 ('WRW :REG_JX:0x048300D0 0x00000001')

  return


# Purge the L2 cache when the test reaches the end of logging
def Regs2out2end () :
  # Wait for some time to allow the write combiner timeout flush to happen
  Minibench.Writetxt2out2 ('\n-- Wait for some time to allow the write combiner timeout flush to happen')
  Minibench.Writetxt2out2 ('IDL 0700')
  # Purge the L2 cache and poll for completion
  Minibench.Writetxt2out2 ('\n-- Purge the L2 cache and poll for completion')
  Minibench.Writetxt2out2 ('WRW :REG_JX:0x048300C8 0x00000001')
  Minibench.Writetxt2out2 ('POL :REG_JX:0x048300C8 0x00000001 0x00000001 0 2500 20000')

  return


# End of FrisaL2.py

