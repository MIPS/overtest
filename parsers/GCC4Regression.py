import re

class GCC4RegressionParser:
  """
  A parser for dejagnu tests
  """
  CONVERT = {"testcases run":"TOTAL",
             "expected passes":"PASS",
             "unexpected failures":"FAIL",
             "expected failures":"XFAIL",
             "unexpected successes":"XPASS",
             "known failures":"KFAIL",
             "unknown successes":"KPASS",
             "warnings":"WARNING",
             "errors":"ERROR",
             "unsupported tests":"UNSUPPORTED",
             "unresolved testcases":"UNRESOLVED",
             "untested testcases":"UNTESTED"}

  def parse(self, sumfilename):
    sumfd = open(sumfilename)
    exp = None
    exppass = True
    expstats = {}
    overallstats = {}

    for l in sumfd.readlines():
      findexp = re.match("^Running .*(testsuite.*\/)(.*\.exp)", l)
      if findexp != None:
        if exp != None:
          self.testsuiteSubmit(exp, exppass, expstats)
          exppass = True
          expstats = {}
        # Found a new group
        exp = findexp.group(1)+findexp.group(2)
      findresult = re.match("^([A-Z]+): (.*)", l)
      if findresult != None:
        result = findresult.group(1)
        if result in ["XPASS", "FAIL", "ERROR"]:
          exppass = False

        if not result in expstats:
          expstats[result] = 1
        else:
          expstats[result] += 1

      if l.startswith("# of "):
        try:
          desc = " ".join(l.split()[2:-1])
          desc = GCC4RegressionParser.CONVERT[desc]
          count = l.split().pop()
          overallstats[desc] = int(count)
        except:
          pass

    if exp != None:
      self.testsuiteSubmit(exp, exppass, expstats)

    sumfd.close()

    return overallstats
