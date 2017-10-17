import os
from Config import CONFIG
from common.NeoBuild import NeoBuild

# AsmExec

class A109000(NeoBuild):
  def __init__(self, data):
    NeoBuild.__init__(self, data)
    self.actionid = 109000
    self.name = "AsmExec"
    self.ccsfile = "metag/tools/pcasm/asm/ccs/meta-as.ccs"
