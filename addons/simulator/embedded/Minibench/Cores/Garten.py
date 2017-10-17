#*****************************************************************************
#
#               file : $RCSfile: Garten.py,v $
#             author : $Author: rst $
#  date last revised : $Date: 2012/07/24 15:56:23 $
#    current version : $Revision: 1.4 $
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
#        description : Meta MiniBench special script fragments for Garten
#
#            defines :
#
#****************************************************************************

import os
#import sys
#from sys import path

#import shutil

def initOut2 () :
  fout2 = open('out2.txt', 'a')

  # Setup Clock frequency
  # This needs to be a 'special' for garten only
  writemsg = '-- Set sys_clk and sb_clk to same frequency as core_clk (Note this is only for Garten)\n'
  fout2.write(writemsg)
  writemsg = 'WRW :REG_META_TB:0x00000110 0x0\n'
  fout2.write(writemsg)
  writemsg = 'WRW :REG_META_TB:0x00000120 0x0\n'
  fout2.write(writemsg)

  fout2.close()

  return


# No additions required in RegDump2out2
def Regs2out2start () :
  return

def Regs2out2end () :
  return


# End of Garten.py

