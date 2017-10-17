import os
from Action import Action
from IMGAction import IMGAction
from common.KernelTest import KernelTest

# META Linux LMbench

class A112264(Action, IMGAction, KernelTest):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 112264
    self.name = "META Linux LMbench"
    self.umask = 0

  # Execute the action.
  def run(self):
    """
    Use the KernelTest framework to grab a pre-built buildroot, kernel and test framework
    Tweak the filesystem so that it has the correct startup scripts
    Use the KernelTest framework to Rebuild the filesystem
    Build LMbench
    Use the KernelTest framework to Put the bootable package together
    Use the KernelTest framework to Run the test
    Process the results
    """
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("LEEDS CVSROOT")

    if not self.fetchLinuxBuildSystem():
      return False

    # Adjust the filesystem
    path = os.path.join(self.testbench_dir, "prepare_test.sh")

    if self.hostHasNetwork():
      cmd = [path, "lmbench", "nfs", self.nfs_server]
    else:
      cmd = [path, "lmbench", "local"]

    if self.execute(workdir=self.buildroot_dir, command=cmd) != 0:
      self.error("Failed to adjust filesystem to boot to LMbench")

    if not self.rebuildFilesystem():
      return False

    if not self.buildKernel():
      return False

    env = {}
    env['PATH'] = "%s:%s" % (self.compiler_path, os.environ['PATH'])

    # Build LMbench for META
    lmbench_module = "metag-lmbench3"
    lmbench_dir = os.path.join(self.getWorkPath(), lmbench_module)

    hostname = self.targetHostname()

    if not self.cvsCheckout(lmbench_module, cvsroot):
      self.error("Failed to check out LMBench")

    if self.execute(workdir=lmbench_dir,
                    env=env,
                    command=["make", "OS=metag-linux-uclibc", "CC=metag-linux-gcc", "AR=metag-linux-ar"]) != 0:
      self.error("Failed to build LMbench")

    if self.execute(workdir=lmbench_dir,
                    env=env,
                    command=["cp", os.path.join(self.testbench_dir, "config", "CONFIG.uclibc"), "bin/metag-linux-uclibc/CONFIG.%s" % hostname]) != 0:
      self.error("Failed to install LMbench config")
 

    # Now that we've built lmbench we need to copy it into the root
    # filesystem.
    if not self.hostHasNetwork():
      # This path should have been created by the prepare_test.sh script.
      if self.installIntoFilesystem(lmbench_dir, "testbench"):
        self.error("Failed to copy LMBench to target path")

      # We've modified the ramdisk so we need to rebuild it and
      # rebuild the kernel.
      if not self.rebuildFilesystem():
        return False

      if not self.buildKernel():
        return False


    if not self.prepareBootloader():
      return False

    result_log_dir = os.path.join(lmbench_dir, "results")
 
    if self.execute(workdir=result_log_dir,
                    env=env,
                    shell=True,
                    command=["rm -rf %s" % os.path.join("metag-linux-uclibc", "*")]) != 0:
      self.error("Failed to remove existing LMbench result files")

    if not self.executeKernelTest():
      return False

    if not self.hostHasNetwork():
      # Because we're executing the tests on the local filesystem we
      # know that the target has no network connection - but we still
      # need a method of extracting the results log.
      #
      # So what we do is get lmbench to spit out the results file
      # across the terminal, capture that data, and write it to the
      # file that processResults() expects.
      console_log = self.fetchOutput().splitlines()

      lmbench_results = ""
      record = False
      for line in console_log:
        if line == "#### OVT START LMBENCH LOG ####":
          record = True
          continue

        if line == "#### OVT END LMBENCH LOG ####":
          record = False
          continue

        if record:
          lmbench_results += line
          lmbench_results += "\n"

      result_file_name = os.path.join(result_log_dir,
                                      "metag-linux-uclibc/%s.0" % hostname)
      f = open(result_file_name, 'w')
      f.write(lmbench_results)
      f.close()

    if not self.processResults(result_log_dir):
      return False

    return True

  def processResults(self, result_log_dir):
    """
    Extract the names and results of tests
    """

    hostname = self.targetHostname()

    result_file_name = os.path.join(result_log_dir, "%s.results" % hostname)

    if self.execute(workdir=result_log_dir,
                    shell = True,
                    command=["make LIST=\"metag-linux-uclibc/*\" > %s" % result_file_name]) != 0:
      self.error("Unable to process results")

    try:
      result_file = open(result_file_name)
    except IOError:
      return self.success({"Result Error":"No result file found"})

    lines = result_file.readlines()[5:]
    result_file.close()

    results = self.lmbench_parse(lines)

    for test in results:
      self.testsuiteSubmit(test, True, results[test])

    self.registerLogFile(result_file_name)
    return True

  def lmbench_parse(self, lines):
    """
    Parse results from an lmbench results file.
  
    The results are returned as a dictionary of dictionaries.
    Each key of the outer dictionary is a test name, and each key
    of the inner dictionary is a field name, e.g.
  
    {"Basic int ops" : {"Host" : "uclibc", "Mhz" : 151},
     "Basic double ops" : {"double add" : 5274.3}}
    """
  
    marker_start = marker_stop = 0
    title = ""
    return_dict = {}
  
    for li in range(len(lines)):
      inner_titles = []
      if "-----------------------------------------------------------------" in lines[li]:
        marker_start = li + 1
        title = lines[marker_start-2]
        if title[0].isspace():
          title = lines[marker_start-3]
        if "-" in title:
          title = title.split("-")[0].strip()
        title = "lmbench_" + title.strip()
        return_dict[title] = {}
      else:
        end = lines[li].split(" ")
        count = 0
  
        insert_list = []
        for i in range(len(end)):
          if "--" in end[i]: count += 1
          if end[i] == "": insert_list.append(i)
          if end[i] == '\n' and i > 2: insert_list.append(1)
  
        if (count+len(insert_list)) == len(end):
          # This is the end of the titles
          marker_stop = li
          sizes = [len(end[0])]
          for k in range(1,len(end)):
            sizes.append(sizes[k-1] + len(end[k]) + 1)
          for i in range(len(end)):
            word = ""
            # Concat words across lines
            for h in range(marker_stop - marker_start):
              prev_size = 0
              if i != 0:
                for k in range(len(end[:i])):
                  prev_size += len(end[k]) + 1
              size = len(end[i])
              word += lines[marker_start + h][prev_size:prev_size+size].strip()
              word += " "
            if word.strip() == "": continue
            inner_titles.append(word.strip())
  
            # Results for each column.
            if i == 0:
              res = lines[marker_stop+1][:sizes[i]]
            else:
              res = lines[marker_stop+1][sizes[i-1]:sizes[i]]
  
            return_dict[title][word.strip()] = res.strip()
    return return_dict

