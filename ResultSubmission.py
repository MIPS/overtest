import os
import sys
from OvertestExceptions import *
from LogManager import LogManager
from TestManager import Testrun
import signal
import getopt

class ResultSubmission:
  def __init__(self, ovtDB):
    """
    Submit a result for an action in a testsuite
    """
    self.ovtDB = ovtDB
    self.log = LogManager(None, True)
    self.ovtDB.registerLog(self.log)
    self.debug=False

  def usage(self, error = None):
    """
    Display the usage
    """
    if error != None:
      self.error(error)
      print ""
    print "Usage:"
    print "OvertestResult [-q] <testname>[:<version>] PASS|FAIL"
    print "      [<field1>:s|i|f:<value1> <field2>:s|i|f:<value2>...]"
    print ""
    print "-q           Operate in query mode instead of submission. The PASS"
    print "             or FAIL operand is not permitted in this mode. With "
    print "             just a testname the stdout will reflect the PASS"
    print "             or FAIL status. If a field is specified, the value of"
    print "             that field is printed. An exit code of 1 indicates"
    print "             test/field not found."
    print ""
    print "QUERY MODE OPTIONS:"
    print "-f <file> --file=<file>"
    print "             Read a series of test/version pairs from a file. This"
    print "             will limit the query to only the test and keys in the"
    print "             file displaying results in the same order as in the"
    print "             file. File format is <test>:<version> per line"
    print "--use-simple"
    print "             Employ simple inference when fetching results. This"
    print "             will work only when versions of tests are requested"
    print "             as results are taken from any similar testsuite"
    print "             instance where there is a test with the same version"
    print "--clone"
    print "             When using simple inference, clone any result that is"
    print "             found in to the current set of results"
    print "--full"
    print "             Display full test result information include the origin"
    print "             of any inferred results"
    print ""
    print "SUBMIT MODE OPTIONS:"
    print "<testname>   can be any string that does not contain a colon ':'"
    print "<version>    can be any string that does not contain a colon and is"
    print "             optional."
    print "             (Versions should ideally be numeric with dot"
    print "              separators)"
    print "PASS|FAIL    specify the overall state of the test"
    print ""
    print "<field1>:s|i|f:<value1>"
    print "Field names can be any string that does not contain a colon ':'"
    print "Data type can be: 's' -> string"
    print "                  'i' -> integer"
    print "                  'f' -> floating point"
    print "Values must convert to the correct type (strings may include colons)"
    print ""
    print "Notes:"
    print "Field names within the same testsuite must always have values of the same"
    print "type. An error will be raised if this is violated."
    print ""
    print "Return code:"
    print "The script will return 0 on success, no output will be printed."
    print "A non-zero return code indicates and error."
    print ""

  def error(self, error):
    """
    Print an error message
    """
    print "ERROR: %s"%error

  def execute(self, args):
    """
    Extract submission id
    Validate testrun status (running, and executing action with testsuiteid)
    Validate host daemon running on this machine with correct pid
    Parse the arguments and submit the result
    """
    if len(args) == 0:
      self.usage()
      return False

    try:
      key = os.environ['__OVERTEST_SUBMISSION_ID__']
    except KeyError:
      self.error("Submission id not set")
      return False
    try:
      (testrunid, testsuiteid, pid) = key.split(":")
      testrunid = int(testrunid)
      testsuiteid = int(testsuiteid)
      pid = int(pid)
    except ValueError:
      self.error("Invalid submission id")
      return False

    mode = "submit"
    query_file = None
    if args[0] == "-q":
      mode = "query"
      use_simple_equivalence = False
      clone_result = False
      self.full_output = False
      try:
        opts, args = getopt.getopt(args, "qcf:", ["use-simple", "clone", "file=", "full"])
      except getopt.GetoptError, e:
        print "ERROR: %s" % str(e)
        self.usage()
        return False

      for (o,a) in opts:
        if o == "--use-simple":
          use_simple_equivalence = True
        elif o in ("-c", "--clone"):
          if not use_simple_equivalence:
            print "ERROR: Clone option must be used in conjunction with --use-simple"
            self.usage()
            return False
          clone_result = True
        elif o in ("-f", "--file"):
          query_file = a
        elif o == "--full":
          self.full_output = True

    self.queryfield = None
    if mode == "submit":
      if len(args) < 2:
        self.usage("Testname/Version and result are required")
        return False
    elif mode == "query":
      if len(args) < 1 and query_file == None:
        testrun = Testrun(self.ovtDB,testrunid=testrunid)
        info = testrun.testsuiteQuery(testsuiteid)
        self.showResults(info, None, info)
        return True

    # <testname>[:<version>] PASS|FAIL [<field1>:s|i|f:<value1> <field2>:s|i|f:<value2>...]
    if query_file == None:
      test = args.pop(0)
      version = None
      try:
        if test.find(":") != -1:
          (test, version) = test.split(":")
      except ValueError:
        self.usage("Bad testname:version. Testname and version must not contain ':'")
        return False

    extendedResults = {}
    if mode == "submit":
      result = args.pop(0)

      if result.upper() == "PASS":
        result = True
      elif result.upper() == "FAIL":
        result = False
      else:
        self.usage("Result must be either PASS or FAIL")
        return False

      for arg in args:
        if arg.count(":") < 2:
          self.usage("Bad format for extended result. <fieldname>:<type>:<value>") 
          return False
        (field, type, value) = arg.split(":", 2)
        if type=="s":
          value = str(value)
        elif type=="i":
          try:
            value = int(value, 0)
          except ValueError:
            self.error("Bad value for field %s type integer: %s"%(field, value))
            return False
        elif type=="f":
          try:
            value = float(value)
          except ValueError:
            self.error("Bad value for field %s type float: %s"%(field, value))
            return False
        else:
          self.usage("Bad type for field %s: %s"%(field, type))
          return False
        extendedResults[field] = value
    else:
      if query_file != None and len(args) != 0:
        self.usage("Test names and field names are not allowed when using a query file")
        return False
      elif len(args) > 1:
        self.usage("Only one field can be specified in query mode")
        return False
      if len(args) == 1:
        if args[0].count(":") != 0:
          self.usage("Only a field name is permitted in query mode")
          return False
        self.queryfield = args[0]

      result = None

    if self.debug:
      print "Testname: %s"%test
      print "Version:  %s"%version
      if mode == "submit":
        print "Result:   %s"%result
      for field in extendedResults:
        print "%s --> %s"%(field, extendedResults[field])
      if self.queryfield != None:
        print "%s" % self.queryfield

    # Now that all the input has been validated do the DB based checks

    # 1) Is the testrun running?
    status = self.ovtDB.getTestrunRunstatus(testrunid)
    if status != "RUNNING" and status != "PAUSED" and status != "EXTERNAL":
      self.error("Testrun is not running or external")
      return False

    # 2) Is the testsuite part of the testrun and running?
    if not self.ovtDB.isTestsuiteRunning(testrunid, testsuiteid, status=="EXTERNAL"):
      self.error("Testsuite is not present or not executing")
      return False
  
    if status != "EXTERNAL":
      # 3) Is the overtest host daemon running?
      try:
        os.kill(pid, signal.SIGUSR2)
      except Exception, e:
        self.error("Failed to find controlling Overtest Host Daemon")
        return False

    # 4) Submit the results
    testrun = Testrun(self.ovtDB,testrunid=testrunid)
    if mode == "submit":
      if version == None:
        testrun.testsuiteSubmit(testsuiteid, test, result, extendedResults)
      else:
        testrun.testsuiteSubmit(testsuiteid, test, result, extendedResults, version)
    elif mode == "query":
      options = {"use_simple_equivalence":use_simple_equivalence}
      options["clone_result"] = clone_result
      if self.queryfield == None:
        options["hide_extended"] = True

      if query_file == None:
        tests = {test:version}
        test_order = [test]
      else:
        try:
          qfile = open(query_file, "r")
        except IOError:
          self.error("Unable to open query file %s" % query_file)
          return False

        tests = {}
        test_order = []
        for line in qfile.readlines():
          line=line.strip(" \n")
          if line.startswith("#") or len(line) == 0:
            continue
          test = line.split(":")
          version = None
          if len(test) == 2:
            version = test[1]
          test=test[0]
          tests[test] = version
          test_order.append(test)
        qfile.close()

      info = testrun.testsuiteQuery(testsuiteid, tests, options=options)
  
      self.showResults(test_order, tests, info)
    
    return True

  def showResults(self, tests, versions, results):
    """
    Display the results of all results in the order specified by results
    """
    bad_results = False
    for test in tests:
      sys.stdout.write("%s" % test)
      if versions != None and versions[test] != None:
        sys.stdout.write(":%s"%versions[test])

      if results == False or len(results) == 0 or not test in results:
        sys.stdout.write("\tNOT FOUND\n")
        bad_results = True
        continue

      if versions == None or versions[test] == None:
        sys.stdout.write(":%s" % (results[test]['version']))

      if self.queryfield == None:
        if results[test]['pass'] == None:
          sys.stdout.write("\tUNSTABLE")
        elif results[test]['pass']:
          sys.stdout.write("\tPASS")
        else:
          sys.stdout.write("\tFAIL")

        if self.full_output:
          if 'inferredfrom' in results[test]:
            sys.stdout.write("\tinferred_from=%s"%results[test]['inferredfrom'])
        sys.stdout.write("\n")
      else:
        if self.queryfield in results[test]['extended']:
          print results[test]['extended'][self.queryfield]
        else:
          print "\tNOT FOUND"
          sys.exit(1)

    if bad_results:
      sys.exit(1)

