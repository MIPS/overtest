from common.NeoBuild import NeoBuild

# LdlkExec

class A109002(NeoBuild):
  def __init__(self, data):
    NeoBuild.__init__(self, data)
    self.actionid = 109002
    self.name = "LdlkExec"
    self.ccsfile = "metag/tools/pcasm/ldlk/ccs/meta-ldlk.ccs"
