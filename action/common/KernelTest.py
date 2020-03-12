#  Copyright (C) 2012-2020 MIPS Tech LLC
#  Written by Matthew Fortune <matthew.fortune@imgtec.com> and
#  Daniel Sanders <daniel.sanders@imgtec.com>
#  This file is part of Overtest.
#
#  Overtest is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3, or (at your option)
#  any later version.
#
#  Overtest is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with overtest; see the file COPYING.  If not, write to the Free
#  Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
#  02110-1301, USA.
import os
import time
from Config import CONFIG
from OvertestExceptions import TestrunAbortedException
from OvertestExceptions import ResourceException
from OvertestExceptions import ConfigException

# META Linux Kernel Test Framework

class KernelTest:
  """
  Helper functions to simplify running Linux Kernel Tests
  """

  def hostHasNetwork(self):
    """
    Return true if the execution host has network connectivity.
    """
    host = self.getResource("Execution Host")
    try:
      features = host.getAttributeValues("Features")
      if "Network" in features:
        return True
      else:
        return False
    except ResourceException:
      return False

  def buildroot_in_cvs(self, version):
    try:
      if version.startswith("METALinux_2_"):
        minor = int(buildroot[12:])
        if minor <= 5:
          return True
    except ValueError:
      pass
    return False

  def initialiseBuildSystem(self):
    buildroot = self.testrun.getVersion("META Linux Buildroot")
    cvs_buildroot = self.buildroot_in_cvs(buildroot)
    if cvs_buildroot:
      self.buildroot_module = "metag-buildroot2"
    else:
      self.buildroot_module = "buildroot"
    self.buildroot_dir = os.path.join(self.getWorkPath(),self.buildroot_module)
    buildroot_shared_dir = os.path.join(self.testrun.getSharedPath("META Linux Buildroot"),self.buildroot_module)

    if buildroot == "METALinux_2_2":
      self.compiler_path = os.path.join(buildroot_shared_dir, "build_metag/staging_dir/usr/bin")
      self.toolkit_path = os.path.join(buildroot_shared_dir, "build_metag/staging_dir/usr")
    elif buildroot in ("METALinux_2_3", "METALinux_2_4", "METALinux_2_5"):
      self.compiler_path = os.path.join(buildroot_shared_dir, "output/build/staging_dir/usr/bin")
      self.toolkit_path = os.path.join(buildroot_shared_dir, "output/build/staging_dir/usr")
    else:
      self.compiler_path = os.path.join(buildroot_shared_dir, "output/host/usr/bin")
      self.toolkit_path = os.path.join(buildroot_shared_dir, "output/host/usr")

  def getTargetBugs(self):
    target_bugs=[]
    try:
      target_bugs = self.config.getVariable("Target Bugs")
      target_bugs = target_bugs.split(",")
    except ConfigException:
      pass
    return target_bugs

  def getBuildrootConfigAndOptions(self):
    """
    Get the config and options based on the Target Board variable. Also
    detect any test which may require C++ and build it too.

    Fall back to old config if the board cannot be determined
    """
    buildroot_options = []
    buildroot = self.testrun.getVersion("META Linux Buildroot")
    cvs_buildroot = self.buildroot_in_cvs(buildroot)
    if cvs_buildroot:
      buildroot_defconfig = "oldconfig"
    else:
      buildroot_defconfig = "chorus2_defconfig"
    if self.testrun.getVersion("Bullet") != None:
      buildroot_options.append("BR2_GCC_CROSS_CXX=y")
      buildroot_options.append("BR2_INSTALL_LIBSTDCPP=y")

    try:
      target_board = self.config.getVariable("Target Board")

      BR2_TARGET_METAG_ATP120_DP_TEST="n"
      BR2_TARGET_METAG_FPGA="n"
      BR2_TARGET_METAG_FPGA_FPU="n"
      BR2_TARGET_METAG_TZ1090_01XX="n"

      if target_board in ("FRISA FPGA", "FRISA2THD FPGA"):
        buildroot_defconfig = "fpga_defconfig"
        # Enable full FP in the toolchain
        if "initfpu" in self.getTargetBugs():
          BR2_TARGET_METAG_FPGA="y"
        else:
          buildroot_options.append("BR2_TARGET_OPTIMIZATION=\"-Os -pipe -mhard-float\"")
          BR2_TARGET_METAG_FPGA_FPU="y"
      elif target_board == "Chorus 2 Metamorph":
        BR2_TARGET_METAG_ATP120_DP_TEST="y"
        buildroot_defconfig = "chorus2_defconfig"
      elif target_board == "COMET Metamorph":
        BR2_TARGET_METAG_TZ1090_01XX="y"
        buildroot_defconfig = "comet_defconfig"
      else:
        self.error("Unknown target board: %s"%target_board)

      buildroot_options.append("BR2_TARGET_METAG_ATP120_DP_TEST=%s"%BR2_TARGET_METAG_ATP120_DP_TEST)
      buildroot_options.append("BR2_TARGET_METAG_FPGA=%s"%BR2_TARGET_METAG_FPGA)
      buildroot_options.append("BR2_TARGET_METAG_FPGA_FPU=%s"%BR2_TARGET_METAG_FPGA_FPU)
      buildroot_options.append("BR2_TARGET_METAG_TZ1090_01XX=%s"%BR2_TARGET_METAG_TZ1090_01XX)
        
    except ConfigException:
      pass

    return (buildroot_defconfig, buildroot_options)

  def fetchLinuxBuildSystem(self):
    """
    Get the pre-prepared test framework
    """
    self.initialiseBuildSystem()
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("LEEDS CVSROOT")

    self.nfs_server= "%s:%s" % (host.getHostName(), self.getWorkPath())

    # Fetch the testbench
    if not self.cvsCheckout("metag-testbench", cvsroot):
      self.error("Failed to check out testbench")

    testbench_module = "metag-testbench"
    self.testbench_dir = os.path.join(self.getWorkPath(), testbench_module)

    buildroot_tgz = os.path.join(self.testrun.getSharedPath("META Linux Buildroot"),
                                 "%s.tgz" % self.buildroot_module)

    # Untar buildroot
    if self.execute(command=["tar", "-xzf", buildroot_tgz]) != 0:
      self.error("Failed to untar buildroot")

    buildroot = self.testrun.getVersion("META Linux Buildroot")

    if buildroot == "METALinux_2_2":
      self.ramdisk_path = os.path.join(self.buildroot_dir,
                                       "binaries/uclibc/rootfs.metag.cpio.gz")
      self.ramdisk_target = "arch/metag/boot/ramdisk/ramdisk.gz"
    elif buildroot in ("METALinux_2_3", "METALinux_2_4", "METALinux_2_5"):
      self.ramdisk_path = os.path.join(self.buildroot_dir,
                                       "output/images/rootfs.cpio.gz")
      self.ramdisk_target = "arch/metag/boot/ramdisk/ramdisk.gz"
    else:
      self.ramdisk_path = os.path.join(self.buildroot_dir,
                                       "output/images/rootfs.cpio")
      self.ramdisk_target = "arch/metag/boot/ramdisk.cpio"

    kernel_module = "metag-linux-2.6"
    kernel_tgz = os.path.join(self.testrun.getSharedPath("META Linux Kernel"),
                              "%s.tgz" % kernel_module)

    # Untar kernel
    if self.execute(command=["tar", "-xzf", kernel_tgz]) != 0:
      self.error("Failed to untar kernel")

    self.kernel_dir = os.path.join(self.getWorkPath(), kernel_module)
    return True

  def rebuildFilesystem(self, extraconfig=None):
    """
    Rebuild the filesystem to incorporate any changes
    """
    # Re-build the filesystem
    command=["make"]
    buildroot_defconfig, buildroot_options = self.getBuildrootConfigAndOptions()
    command += buildroot_options
    if extraconfig != None:
      command.extend(extraconfig)
    if self.execute(workdir=self.buildroot_dir,
                    command=command) != 0:
      self.error("Failed to build BuildRoot")

    # Install the new filesystem
    if self.execute(workdir=self.kernel_dir,
                    command=["cp", self.ramdisk_path, self.ramdisk_target]) != 0:
      self.error("Failed to copy ramdisk")
    return True

  def buildKernel(self, config_override=None, prepare=False):
    # Set the build environment
    env = {}
    env['PATH'] = "%s:%s" % (self.compiler_path, os.environ['PATH'])

    if config_override == None:
      config_override = {}

    kernel_config = self.config.getVariable("Kernel Config")
    if kernel_config == "":
      # Decide which config to use
      target_board = self.getResource("Target Board")
      # 1) Is it an SoC or an FPGA
      board_type = target_board.getAttributeValue("Board Type")
      if board_type == "SoC":
        soc_type = target_board.getAttributeValue("SoC Type")
        if soc_type in ("COMET ES1", "COMET PS1"):
          kernel_action_version = self.testrun.getVersion("META Linux Kernel")
          if kernel_action_version in ("METALinux_2_2", "METALinux_2_3", "METALinux_3_1"):
            kernel_config = "comet_defconfig"
          else:
            kernel_config = "tz1090_defconfig"
        elif soc_type == "METAMORPH C2":
          kernel_config = "chorus2_defconfig"
        else:
          self.error("Unknown SoC Type: %s" % soc_type)
      elif board_type == "FPGA":
        cores = target_board.getAttributeValues("Core Revision")
        if len(cores) == 1:
          core = cores[0]
        else:
          core = target_board.getRequestedAttributeValue("Core Revision")
        if core in ["META2", "META213", "COMET", "FRISA", "FRISA2THD"]:
          kernel_config = "meta2_defconfig"
          try:
            if self.config.getVariable("SMP"):
              kernel_config = "meta2_smp_defconfig"
          except:
            pass
        elif core == "META122":
          kernel_config = "meta1_defconfig"
        else:
          self.error("Unsupported core for Linux kernel: %s" % core)
      else:
        self.error("Unrecognised board type: %s"%board_type)

    # Enable halt on panic for new kernels
    if not self.testrun.getVersion('META Linux Kernel') in ('METALinux_2_2', 'METALinux_2_3', 'Latest 07.11.11'):
      config_override['CONFIG_META_HALT_ON_PANIC'] = 'y'

    if "l2cache" in self.getTargetBugs():
      config_override['CONFIG_META_L2C'] = 'n'

    # Override any config settings from the caller
    if len(config_override) != 0:
      config_file = open(os.path.join(self.kernel_dir, "arch", "metag", "configs", kernel_config), "r")
      config_content = config_file.read()
      config_file.close()
      config_file = open(os.path.join(self.kernel_dir, "arch", "metag", "configs", kernel_config), "w")
      for line in config_content.split("\n"):
        ignore_line = False
        for override in config_override:
          if line.startswith("%s=" % override) or \
             line.startswith("# %s is not set" % override):
            ignore_line = True

        if not ignore_line:
          config_file.write("%s\n"%line)
      for override in config_override:
        config_file.write("%s=%s\n"%(override, config_override[override]))
      config_file.close()

    # Configure the kernel appropriately
    if self.execute(workdir=self.kernel_dir,
                    env=env,
                    command=["make", "ARCH=metag",
                                     "CROSS_COMPILE=metag-linux-",
                                     kernel_config]) != 0:
      self.error("Failed to create default config")

    kernel_command = ["make", "ARCH=metag",
                              "CROSS_COMPILE=metag-linux-"]

    if prepare:
      kernel_command.append("modules_prepare")

    # Re-build the kernel with the new filesystem
    if self.execute(workdir=self.kernel_dir,
                    env=env,
                    command=kernel_command) != 0:
      self.error("Failed to build kernel")

    return True

  def prepareBootloader(self, bootloader_suffix=False, fpgatimer=None):
    """
    Prepare the bootable package including the linux kernel

    The 'bootloader_suffix' argument indicates whether a string should
    be appended to the bootloader target. For example, specifying
    "_btc" as the suffix causes a Bash The Cache bootloader
    configuration to be created.

    The 'fpgatimer' argument indicates that the fpga wrapper should be
    configured to look like a specific frequency regardless of the actual
    frequency
    """
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("LEEDS CVSROOT")

    bootloader_version = self.testrun.getVersion("META Linux Bootloader")

    bootloader_tag = "HEAD"
    if bootloader_version != None and bootloader_version != "Latest":
      bootloader_tag = bootloader_version

    # Fetch the bootloader
    if not self.cvsCheckout("meta-bootloader", cvsroot, tag=bootloader_tag):
      self.error("Failed to check out meta-bootloader")

    # Figure out what kind of bootloader to build
    bootloader_board = self.config.getVariable("Bootloader Board")
    if bootloader_board == "":
      # Decide which board to use
      target_board = self.getResource("Target Board")
      # 1) Is it an SoC or an FPGA
      board_type = target_board.getAttributeValue("Board Type")
      if board_type == "SoC":
        soc_type = target_board.getAttributeValue("SoC Type")
        if soc_type == "COMET ES1":
          bootloader_board = "comet_eval"
        elif soc_type == "COMET PS1":
          bootloader_board = "comet_metamorph_ps1"
        elif soc_type == "METAMORPH C2":
          bootloader_board = "metamorph"
        else:
          self.error("Unknown SoC Type: %s" % soc_type)
      elif board_type == "FPGA":
        cores = target_board.getAttributeValues("Core Revision")
        if len(cores) == 1:
          core = cores[0]
        else:
          core = target_board.getRequestedAttributeValue("Core Revision")
        if core in ["META2", "META213", "COMET", "FRISA", "FRISA2THD"]:
          fpga_type = target_board.getAttributeValue("FPGA Type")
          if fpga_type == "TCF":
            bootloader_board = "meta2_tcf"
            execution_board = self.config.getVariable("Target Board")
            if execution_board in ("FRISA FPGA", "FRISA2THD FPGA"):
              bootloader_board = "frisa_tcf"
            try:
              if self.config.getVariable("SMP"):
                if execution_board in ("FRISA FPGA", "FRISA2THD FPGA"):
                  bootloader_board = "frisa_tcf_smp"
                else:
                  self.error("SMP not supported for %s" % execution_board)
            except:
              pass
          else:
            bootloader_board = "meta2_fpga"
        elif core == "META122":
          bootloader_board = "meta1_fpga"
        else:
          self.error("Unsupported core for Linux kernel: %s" % core)
      else:
        self.error("Unrecognised board type: %s"%board_type)

    # If the user hasn't requested a specific bootloader we claim we
    # know better.
    if bootloader_suffix and not self.config.getVariable("Bootloader Board"):
      bootloader_board += bootloader_suffix

    # Build the bootloader
    env = {}
    env['METAG_INST_ROOT'] = self.config.getVariable('METAG_INST_ROOT')
    cmd = ["make", "BOARD=%s" % bootloader_board]

    # Add the modified fpga timer value
    if fpgatimer != None:
      extra_imgfile = os.path.join(self.getWorkPath(), "fpgatimer.img")
      imgfile = open(extra_imgfile, "w")
      imgfile.write("MWR 0x03000040 0x%x\n" % (int(fpgatimer)-1))
      imgfile.close()
      cmd.append("EXTRA_IMGFILES=%s" % extra_imgfile)

    if self.execute(workdir=os.path.join(self.getWorkPath(), "meta-bootloader"),
                    env=env,
                    command=cmd) != 0:
      self.error("Failed to build bootloader")

    if self.execute(workdir=self.kernel_dir,
                    command=["cp", "arch/metag/boot/vmlinux.bin",
                                   os.path.join(self.getWorkPath(), "meta-bootloader")]) != 0:
      self.error("Failed to copy kernel image to bootloader")

    return True

  def executeKernelTest(self):
    """
    Run the bootloader to boot the kernel and run a test
    """
    run_dir = os.path.join(self.getWorkPath(), "meta-bootloader")
    bootjs_filename = os.path.join(run_dir, "boot.js")
    debug_adapter = self.getResource("Debug Adapter")
    script_name = debug_adapter.getAttributeValue("DA Name")

    result = self.execute(command=[CONFIG.neo, '-q', 'run_dascript', 
                                   os.path.join(self.testbench_dir, 'kerneltest.py'), 
                                   '-T', '18000', 
                                   '-D', str(script_name), 
                                   '-F', str(run_dir),
                                   bootjs_filename])

    self.registerLogFile(self.fetchOutputFile())
    if result == 0:
      return self.success()
    else:
      self.error("Failed to run kernel test")

  def installIntoFilesystem(self, src_path, dest_path):
    """
    Install a file into the specified relative path on the target

    Returns 0 on success.
    """
    buildroot = self.testrun.getVersion("META Linux Buildroot")

    if buildroot == "METALinux_2_2":
      install_path = os.path.join(self.buildroot_dir, "project_build_metag",
                                  "uclibc", "root", dest_path)
    else:
      install_path = os.path.join(self.buildroot_dir, "output", "target",
                                  dest_path)

    return self.execute(command=["cp", "-a", src_path, install_path])

  def targetHostname(self):
    """
    Get the configured hostname of a target
    """
    buildroot = self.testrun.getVersion("META Linux Buildroot")

    if buildroot == "METALinux_2_2":
      return "uclibc"
    else:
      return "buildroot"
