#  Copyright (C) 2012-2020 MIPS Tech LLC
#  Written by Matthew Fortune <matthew.fortune@imgtec.com> and
#  Daniel Sanders <daniel.sanders@imgtec.com>
#  This file is part of Overtest.
#
#  Overtest is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3, or (at your option)
#  any later version.
#
#  Overtest is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with overtest; see the file COPYING.  If not, write to the Free
#  Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
#  02110-1301, USA.

import Minibench


# *************** Register setup for dtest_sdxx.ldr *************** #


def ProgInfo():
  Name = "MTX"
  GeneratingScript = "mtx.py"
  return (Name, GeneratingScript)

def LoadDnl(dnlname):
  Minibench.RepProg("DNL Load")
  # By default it will load <out.dnl>")
  Minibench.Com("Loading DNL state <out.dnl>")
  # You could specify the name of dnl file to be loaded here
  if dnlname == None :
    Minibench.LoadDnl("out.dnl")
  else :
    Minibench.LoadDnl(dnlname)
  return

def ConfigRegs():
  # Nothing needed for MTX
  return

def SetThreads():

  # Setup thread 0
  Minibench.RepProg("Setup Thread 0")

  # MTX does not setup SP

  # PC setup uses namespace :REG_MTX:
  Minibench.MtxRegWrite("000000F8", "80900000")
  Minibench.MtxRegWrite("000000FC", "00000005")
  Minibench.MtxRegPol("000000FC", "80000000", "80000000", 0)

  return

def ThreadsMask():
  return("00000001")

def StartThreads():
  Minibench.RepProg("Start Threads")
  Minibench.MtxRegWrite("00000000", "00000001")
#  Minibench.MtxRegPol("00000000", "00000000", "00000001", 0, 0)
  return

def PollforTestEnd():
  #Minibench.RepProg("Poll for Test End ")
  #Minibench.RegPol("04800000", "00000000", "00000001", 0, 0)
  Minibench.MtxRegPol("00000000", "00000000", "00000001", 0, 0)
  return

