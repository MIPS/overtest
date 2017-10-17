import os

class KeyMaker:
  """
  Generates MD5 keys
  """
  def getVerifyMD5Keys(self, directory, type, info_on=0):

    if type == "static":
      style = "ST"
    elif type == "FPGA":
      style = "FP"
    else:
      self.error("Unknown build type: %s\n", type)
      
    verifyMD5Keys = {}
    for root, dirs, files in os.walk(directory):
      # Get the keymaker
      for file in files:
        if not file.endswith(".tgz"):
          continue
        # Now see if this is a non-standard style:
        res = self.execute(command=["tar", "-O", "-xzf", os.path.join(root, file), "%s/runtype.txt" % (file[:-4])])
        if res != 0:
          self.proccount -= 1
          continue
        
        runtype = self.fetchOutput().strip().rstrip("\n")
        self.proccount -= 1
        
        newstyle=style
        if runtype == "RUNTYPE=NSIM":
          newstyle="NS"
        elif runtype == "RUNTYPE=STATIC-SIM":
          newstyle="ST"
        elif runtype == "RUNTYPE=INSCRIPT":
          newstyle="IN"
        elif runtype == "RUNTYPE=FPGA":
          newstyle="FP"

        key = self.neoKeyMaker(os.path.join(root, file), newstyle, info_on)
        if key != None:
          verifyMD5Keys[file[:-4]] = key

    return verifyMD5Keys
