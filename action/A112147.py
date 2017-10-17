from common.NeoBuild import NeoBuild

# TbiCore

class A112147(NeoBuild):
  def __init__(self, data):
    NeoBuild.__init__(self, data)
    self.actionid = 112147
    self.name = "TbiCore"
    self.ccsfile = "metag/tools/ccs/tbi-core.ccs"
