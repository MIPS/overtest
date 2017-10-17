from common.NeoBuild import NeoBuild

# LinkerExec

class A109001(NeoBuild):
  def __init__(self, data):
    NeoBuild.__init__(self, data)
    self.actionid = 109001
    self.name = "LinkerExec"
    self.ccsfile = "metag/tools/pcasm/link/ccs/meta-ld.ccs"
