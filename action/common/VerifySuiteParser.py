
class VerifySuiteParser:
  """
  A parser to read a log file from a verify run and submit the
  results found
  """
  def parseVerifyResults(self, filename, md5Results = None):
    """
    Read the file and analyse the results
    """
    file = open(filename, "r")
    summary = {}
    results_started = False
    results_finished = False
    line = file.readline()
    while line != "":
      # First of all find the start of the results
      if not results_started:
        if line == "Final report\n":
          # Skip the table header
          line = file.readline()
          results_started = True
        # Move to the next line
        line = file.readline()
        continue
      
      if not results_finished:
        if line.startswith("Of ") or line.startswith("In "):
          results_finished = True

      # Now we have the real results (or the summary)
      if results_finished:
        # Process the summary
        if line.endswith("failed to run successfully\n"):
          # A non-regex way of finding the 1 in:
          # "Of 49 tests, 1 failed to run successfully"
          count = line[line.find(",")+2:][:line[line.find(",")+2:].find(" ")]
          if count.isdigit():
            summary['Run Failures'] = int(count)
        elif line.endswith("failed to simulate\n"):
          count = line[line.find(",")+2:][:line[line.find(",")+2:].find(" ")]
          if count.isdigit():
            summary['Sim Failures'] = int(count)
        elif line.endswith("Unexpected error(s) found\n"):
          count = line[line.find(",")+2:][:line[line.find(",")+2:].find(" ")]
          if count.isdigit():
            summary['Unexpected Errors'] = int(count)
        elif line.endswith("Unexpected fail(s) found\n"):
          count = line[line.find(",")+2:][:line[line.find(",")+2:].find(" ")]
          if count.isdigit():
            summary['Unexpected Fails'] = int(count)
        elif line.endswith("released\n"):
          count = line[line.find(",")+2:][:line[line.find(",")+2:].find(" ")]
          if count.isdigit():
            summary['Release Count'] = int(count)
          count = line[line.find(" ")+1:][:line[line.find(" ")+1:].find(" ")]
          if count.isdigit():
            summary['Total'] = int(count)
          # This is the last interesting line in a report
          break
      else:
        extended_results = {}
        # Process a test result
        # "Test  49 mlib4     Pass  Pass Completed  Yes"
        columns = line.split()
        testname = columns[2]
        build = columns[3]
        run = columns[4]
        sim = columns[5]
        # Released is always the last column (5th column may not exist)
        released = columns[len(columns)-1]

        # Convert the results to booleans
        extended_results['Build'] = (build == "Pass")
        extended_results['Released'] = (released == "Yes")
        
        success = extended_results['Build'] and extended_results['Released']
        if run == "NSIM" or run == "FPGA":
          # Do not store a run result for an FPGA or NSIM test
          run = None
          sim = None
        else:
          extended_results['Run'] = (run == "Pass")
          extended_results['Sim'] = (sim == "Completed")
          success = success and extended_results['Run'] and extended_results['Sim']

        version = None
        if md5Results != None:
          version = md5Results.get(testname)

        # Now submit the result
        self.testsuiteSubmit(testname, success, extended_results, version=version)

      # Move to the next result
      line = file.readline()
    return summary

