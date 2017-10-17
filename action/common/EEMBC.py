class EEMBCAction:
  """
  Common functionality for EEMBC Build and Run stages
  """
  def fetchBmarkList(self, workdir, platform):
    """
    Fetch a list of benchmarks that will run based on the platform
    """
    bmarks_mk = ("include consumer_lite/dirsv2%s.mak" % platform) +\
                "\n" +\
                "all:\n" +\
                "\t@echo $(bmarks)\n"

    bmarks_mkfile = open("%s/eembc/bmark.mk" % workdir, "w")
    bmarks_mkfile.write(bmarks_mk)
    bmarks_mkfile.close()

    result = self.execute (command=["make", "-f", "bmark.mk"],
                           workdir="%s/eembc" % workdir)

    if result != 0:
      self.error ("Failed to determine bmark list")

    bmarks = self.fetchOutput()
    return bmarks.strip().split(" ")
