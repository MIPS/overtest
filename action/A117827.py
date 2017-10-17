import os
import glob
from Action import Action
from Config import CONFIG
from parsers.GCC4Regression import GCC4RegressionParser

# Basic tools QA

class A117827(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117827
    self.name = "Basic tools QA"

  def _addConfig(self, config, option, value):
    if value != "":
      config.append(option % value)

  # Execute the action.
  def run(self):
    triple = self.config.getVariable("Triple")
    toolchain_root = self.config.getVariable("Toolchain Root")

    gcc_exec = os.path.join(toolchain_root, "bin", "%s-gcc" % triple)

    cflags = self.config.getVariable("CFLAGS")
    # This is 32, n32 or 64
    abi = self.config.getVariable("ABI")
    # This is el or eb
    endian = self.config.getVariable("Endian")

    env = {}

    if endian == "el":
      cflags = "-mabi=%s -EL %s" % (abi, cflags)
    else:
      cflags = "-mabi=%s -EB %s" % (abi, cflags)

    if self.version.startswith("QEMU"):
      qemu_root = self.config.getVariable("QEMU Root")
      cpu = self.config.getVariable("CPU")
      if triple.endswith("linux-gnu"):
        if abi == "32":
	  suffix = ""
        else:
	  suffix = abi
        if endian == "el":
	  suffix = "%sel" % suffix
        qemu_exec = os.path.join(qemu_root, "bin", "qemu-mips%s" % suffix)
        qemu_opts = "-r 2.6.38 -cpu %s" % cpu
      else:
        if abi == "32":
  	  suffix = ""
        else:
  	  suffix = "64"
        if endian == "el":
  	  suffix = "%sel" % suffix
        qemu_exec = os.path.join(qemu_root, "bin", "qemu-system-mips%s" % suffix)
	qemu_opts = "-cpu %s -semihosting -nographic -kernel" % cpu
	if abi == "32":
	  ldscript = "-Tuhi32.ld"
        elif abi == "n32":
	  ldscript = "-Tuhi64_n32.ld"
        else:
	  ldscript = "-Tuhi64_64.ld"
	ldflags = "-Wl,--defsym,__memory_size=32M %s" % ldscript

    passcount = 0

    # Stupid test!
    fd = open(os.path.join(self.getWorkPath(), "hello.c"), "w")
    fd.write("#include <stdio.h>\n")
    fd.write("\n")
    fd.write("int main() {")
    fd.write("printf(\"Hello World!\");\n")
    fd.write("return 0;\n")
    fd.write("}")
    fd.close()

    command = [ "%s %s %s hello.c -o hello.elf" % (gcc_exec, cflags, ldflags) ]

    result = self.execute(env=env, command=command, shell=True)

    if result != 0:
      self.error("Failed to build test")

    command = [ "%s %s ./hello.elf" % (qemu_exec, qemu_opts) ]

    result = self.execute(env=env, command=command, shell=True, timeout=10)

    if result != 0:
      self.error("Failed to run test")

    output = self.fetchOutput()

    self.testsuiteSubmit("helloworld", output == "Hello World!", { "output" : output })
    if output == "Hello World!":
      passcount += 1

    return self.success({ "PASS" : passcount, "FAIL" : 0})
