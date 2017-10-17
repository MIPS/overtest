
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

