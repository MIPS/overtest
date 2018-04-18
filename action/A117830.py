import os
import glob
from Action import Action
from Config import CONFIG
from parsers.GCC4Regression import GCC4RegressionParser
import re

# G++ Test

class A117830(Action, GCC4RegressionParser):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117830
    self.name = "G++ Test"

  def _addConfig(self, config, option, value):
    if value != "":
      config.append(option % value)

  # Execute the action.
  def run(self):
    dejagnu = os.path.join(self.testrun.getSharedPath("Dejagnu"), "dejagnu")
    gcc = os.path.join(self.testrun.getSharedPath("GCC"), "gcc")

    triple = self.config.getVariable("Triple")
    toolchain_root = self.config.getVariable("Toolchain Root")

    gcc_exec = os.path.join(toolchain_root, "bin", "%s-gcc" % triple)
    gpp_exec = os.path.join(toolchain_root, "bin", "%s-g++" % triple)
    test_installed = os.path.join(gcc, "contrib", "test_installed")

    testSelection = self.config.getVariable("GCC Test Selection")
    cflags = self.config.getVariable("CFLAGS")
    # This is 32, n32 or 64
    abi = self.config.getVariable("ABI")
    # This is el or eb
    endian = self.config.getVariable("Endian")

    env = {}
    env['PATH'] = CONFIG.makeSearchPath([os.path.join(toolchain_root, "bin"),
					 "/user/rgi_data2/Verify/CentOS-5/Tcl_8.6.4_x64/root/bin",
					 dejagnu, os.environ['PATH']])

    if triple.startswith("nanomips"):
      if abi == "p32":
	abi_opt = "-m32"
      elif abi == "p64":
	abi_opt = "-m64"
      else:
	self.error("unknown abi %s" % abi)
    else:
      abi_opt = "-mabi=%s" % abi

    if endian == "el":
      cflags = "%s -EL %s" % (abi_opt, cflags)
    else:
      cflags = "%s -EB %s" % (abi_opt, cflags)

    cflags = "/%s" % cflags.replace(" ", "/")

    extra_command = []

    if self.version.startswith("QEMU"):
      qemu_root = self.config.getVariable("QEMU Root")
      cpu = self.config.getVariable("CPU")
      if triple.endswith("linux-gnu") or triple.endswith("linux-musl"):
        board = "multi-sim"
        if abi == "32" or abi == "p32":
	  suffix = ""
        else:
	  suffix = abi
	if triple.startswith("nanomips"):
	  if endian == "eb":
	    suffix = "%seb" % suffix
	  qemu_exec = os.path.join(qemu_root, "bin", "qemu-nanomips%s" % suffix)
	else:
	  if endian == "el":
	    suffix = "%sel" % suffix
	  qemu_exec = os.path.join(qemu_root, "bin", "qemu-mips%s" % suffix)
        env['DEJAGNU_SIM'] = qemu_exec
        env['DEJAGNU_SIM_OPTIONS'] = "-r 4.5.0 -cpu %s" % cpu
        env['DEJAGNU_SIM_GCC'] = gcc_exec
      else:
        board = "generic-sim"
        if abi == "32" or abi == "p32":
  	  suffix = ""
        else:
  	  suffix = "64"
	if triple.startswith("nanomips"):
	  cpu = "nanomips-generic"
	  if endian == "eb":
	    suffix = "%seb" % suffix
	  qemu_exec = os.path.join(qemu_root, "bin", "qemu-system-nanomips%s" % suffix)
	else:
	  if endian == "el":
	    suffix = "%sel" % suffix
	  qemu_exec = os.path.join(qemu_root, "bin", "qemu-system-mips%s" % suffix)
	env['DEJAGNU_SIM'] = qemu_exec
	env['DEJAGNU_SIM_OPTIONS'] = "-cpu %s -semihosting -nographic -kernel" % cpu
	if abi in ("32", "p32"):
	  env['DEJAGNU_SIM_LDSCRIPT'] = "-Tuhi32.ld"
        elif abi == "n32":
	  env['DEJAGNU_SIM_LDSCRIPT'] = "-Tuhi64_n32.ld"
        else:
	  env['DEJAGNU_SIM_LDSCRIPT'] = "-Tuhi64_64.ld"
	env['DEJAGNU_SIM_LINK_FLAGS'] = "-Wl,--defsym,__memory_size=32M"
    elif self.version == "GNUSIM":
      extra_command.append("SIM=%s" % os.path.join(toolchain_root, "bin", "%s-run" % triple))
      if abi in ("32", "p32"):
	board = "mips-sim-mti32"
      elif abi == "n32":
	board = "mips-sim-mti64_n32"
      elif abi == "64":
	board = "mips-sim-mti64_64"
      else:
        self.error("Unknown ABI")

    # Add the HOSTCC and HOSTCFLAGS variables for build programs
    self.setHostCC(test_installed)

    command = [test_installed, "--without-gfortran", "--without-objc", "--without-gcc",
	       "--with-g++=%s" % gpp_exec,
	       "--prefix=%s" % toolchain_root,
	       "--target=%s" % triple,
	       "--target_board=%s%s" % (board, cflags)]

    if testSelection != "":
       command.append(testSelection)

    command.extend(extra_command)

    result = self.execute(env=env, command=command)

    if result != 0:
      self.error("Failed to run testsuite")

    self.registerLogFile(os.path.join (self.getWorkPath(), "g++.log"), compress=True)
    self.registerLogFile(os.path.join (self.getWorkPath(), "g++.sum"), compress=True)

    summary = self.parse (os.path.join (self.getWorkPath(), "g++.log"))

    return self.success(summary)

  def setHostCC(self, test_installed):
    """
    Add the HOSTCC and HOSTCFLAGS entried to test_installed if they are missing
    Also unconditionally set the GCC_UNDER_TEST variable
    """
    with open(test_installed, 'r') as f:
      lines = list(f)
    try:
      lines.index("set HOSTCC \"gcc\"\n")
    except ValueError, e:
      index = lines.index("set CFLAGS \"\"\n")
      lines.insert(index,"set HOSTCC \"gcc\"\n")
      lines.insert(index,"set HOSTCFLAGS \"\"\n")
    try:
      idx = lines.index("set GCC_UNDER_TEST \"${GCC_UNDER_TEST-${prefix}${prefix+/bin/}${target+$target-}gcc}\"\n")
      lines[idx] = "set GCC_UNDER_TEST \"${prefix}${prefix+/bin/}${target+$target-}gcc\"\n"
    except ValueError, e:
      pass
    with open(test_installed, 'w') as f:
      f.write("".join(lines))
