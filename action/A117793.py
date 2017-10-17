from common.NeoBuild import NeoBuild

# MeOSLib

class A117793(NeoBuild):
  def __init__(self, data):
    NeoBuild.__init__(self, data)
    self.actionid = 117793
    self.name = "MeOSLib"
    self.ccsfile = "metag/tools/libs/meos/ccs/meoslib.ccs"
