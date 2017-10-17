import os
from Action import Action
from IMGAction import IMGAction
from common.KernelTest import KernelTest
from OvertestExceptions import *
from Config import CONFIG

# META Linux BTC

class A116323(Action, IMGAction, KernelTest):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116323
    self.name = "META Linux BTC"
    self.umask = 0

  # Execute the action.
  def run(self):
    """
    Use the KernelTest framework to grab a pre-built buildroot and test framework
    Use the KernelTest framework to rebuild the filesystem
    Use the KernelTest framework to build the kernel
    Use the KernelTest framework to Put the bootable package together
    Use the KernelTest framework to Run the test
    Process the results
    """
    if not self.fetchLinuxBuildSystem():
      return False

    # Adjust the filesystem
    path = os.path.join(self.testbench_dir, "prepare_test.sh")

    if self.hostHasNetwork():
      cmd = [path, "btc", "nfs", self.nfs_server]
    else:
      cmd = [path, "btc", "local"]

    if self.execute(workdir=self.buildroot_dir, command=cmd) != 0:
      self.error("Failed to adjust filesystem to boot BTC")

    if not self.rebuildFilesystem():
      return False

    if not self.buildKernel():
      return False

    if not self.prepareBootloader(bootloader_suffix="_btc"):
      return False

    try:
      run_dir = os.path.join(self.getWorkPath(), "meta-bootloader")
      bootjs_filename = os.path.join(run_dir, "boot.js")
      debug_adapter = self.getResource("Debug Adapter")
      script_name = debug_adapter.getAttributeValue("DA Name")

      cmd = [CONFIG.neo, '-q', 'onetest', '-T', '3600',
             '-D', str(script_name), '-F', str(run_dir), bootjs_filename]

      result = self.execute(command=cmd)
    except TimeoutException, e:
      self.error("Timeout when running BTC")

    if result == 0:
      ret = self.success()
    else:
      ret = self.error("Failed to run BTC")

    self.testsuiteSubmit("META Linux BTC", ret)
    return self.success({"Pass count":1})
