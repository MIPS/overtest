from copy import deepcopy
import sys
from TestrunEditing import TestrunOptions

class GNUTestConfig:

  def __init__(self):
    self.tot = False

  def get_p32_elf_configs(self):
    test_config = []
    t = self.testDefinition("elf")
  
    options = {}
    options['Manual Triple'] = "nanomips-elf"
    t.config['MIPS Prebuilt'] = options

    options = {}
    options['ABI'] = "p32"
    t.config['MIPS Test'] = options
  
    #options['Endian'] = "Big"
  
    #options['CFLAGS'] = "-msoft-float"
    #t.description = "R6 Bare Metal - BE,P32,SF"
    #test_config.append(deepcopy(t))
  
    #options['CFLAGS'] = "-mhard-float"
    #t.description = "R6 Bare Metal - BE,P32,HF"
    #test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"

    options['CFLAGS'] = "-msoft-float"
    t.description = "R6 Bare Metal - LE,P32,SF"
    test_config.append(deepcopy(t))

    options['CFLAGS'] = "-msoft-float -mcmodel=medium"
    t.description = "R6 Bare Metal - LE,P32,SF,MED"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-msoft-float -mcmodel=large"
    t.description = "R6 Bare Metal - LE,P32,SF,LRG"
    test_config.append(deepcopy(t))

    options['CFLAGS'] = "-msoft-float -mpid"
    t.description = "R6 Bare Metal - LE,P32,SF,PID"
    test_config.append(deepcopy(t))

    options['CFLAGS'] = "-msoft-float -mcmodel=medium -mpid"
    t.description = "R6 Bare Metal - LE,P32,SF,MED,PID"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-msoft-float -mcmodel=large -mpid"
    t.description = "R6 Bare Metal - LE,P32,SF,LRG,PID"
    test_config.append(deepcopy(t))

    options['CFLAGS'] = "-msoft-float -mno-gpopt"
    t.description = "R6 Bare Metal - LE,P32,SF,NGP"
    test_config.append(deepcopy(t))

    options['CFLAGS'] = "-msoft-float -mcmodel=medium -mno-gpopt"
    t.description = "R6 Bare Metal - LE,P32,SF,MED,NGP"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-msoft-float -mcmodel=large -mno-gpopt"
    t.description = "R6 Bare Metal - LE,P32,SF,LRG,NGP"
    test_config.append(deepcopy(t))

    options['CFLAGS'] = "-msoft-float -mno-gpopt -mno-pcrel"
    t.description = "R6 Bare Metal - LE,P32,SF,NGP,NPC"
    test_config.append(deepcopy(t))

    options['CFLAGS'] = "-msoft-float -mcmodel=medium -mno-gpopt -mno-pcrel"
    t.description = "R6 Bare Metal - LE,P32,SF,MED,NGP,NPC"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-msoft-float -mcmodel=large -mno-gpopt -mno-pcrel"
    t.description = "R6 Bare Metal - LE,P32,SF,LRG,NGP,NPC"
    test_config.append(deepcopy(t))

    options['CFLAGS'] = "-msoft-float -fpic"
    t.description = "R6 Bare Metal - LE,P32,SF,pic"
    test_config.append(deepcopy(t))

    options['CFLAGS'] = "-msoft-float -mcmodel=medium -fpic"
    t.description = "R6 Bare Metal - LE,P32,SF,MED,pic"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-msoft-float -mcmodel=medium -fPIC"
    t.description = "R6 Bare Metal - LE,P32,SF,MED,PIC"
    test_config.append(deepcopy(t))
  
    #options['CFLAGS'] = "-mhard-float"
    #t.description = "R6 Bare Metal - LE,P32,HF"
    #test_config.append(deepcopy(t))

    #options['CFLAGS'] = "-msoft-float -march=32r6s"
    #t.description = "R6 Bare Metal - LE,P32,SF,NMS"
    #test_config.append(deepcopy(t))
  
    return test_config
  
  def get_p32_linux_configs(self):
    test_config = []
    t = self.testDefinition("linux")

    options = {}
    options['Manual Triple'] = "nanomips-linux-musl"
    t.config['MIPS Prebuilt'] = options
  
    options = {}
    options['ABI'] = "p32"
    t.config['MIPS Test'] = options
  
    #options['Endian'] = "Big"
  
    #options['CFLAGS'] = "-msoft-float"
    #t.description = "R6 Linux - BE,P32,SF"
    #test_config.append(deepcopy(t))
  
    #options['CFLAGS'] = "-mhard-float"
    #t.description = "R6 Linux - BE,P32,HF"
    #test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"
  
    #options['CFLAGS'] = "-msoft-float"
    #t.description = "R6 Linux - LE,P32,SF"
    #test_config.append(deepcopy(t))
  
    #options['CFLAGS'] = "-mhard-float"
    #t.description = "R6 Linux - LE,P32,HF"
    #test_config.append(deepcopy(t))
  
    return test_config
  
class PrefixedTestrunOptions(TestrunOptions):
  def __init__(self, prefix):
    TestrunOptions.__init__(self, "new")
    self.descriptionPrefix = prefix

  # Override the description to allow the test configurations to just
  # specify the name of the variant and something else provide the
  # description of the actual test
  @property
  def description(self):
    if self.descriptionPrefix != None:
      return "%s - %s" % (self.descriptionPrefix, self._description)
    else:
      return self._description

  @description.setter
  def description(self, value):
    self._description = value

class GCCDejagnuTestConfig(GNUTestConfig):
  def __init__(self, use_gnusim = False):
    GNUTestConfig.__init__(self)
    self.use_gnusim = use_gnusim

  def testDefinition(self, os_part):
    t = PrefixedTestrunOptions("GCC Test")

    if os_part == "elf":
      if self.use_gnusim:
	t.tasks['MIPS Testing'] = { "GCC Test" : "GNUSIM" }
      else:
	t.tasks['MIPS Testing'] = { "GCC Test" : "QEMU System Emulator" }
    else:
      t.tasks['MIPS Testing'] = { "GCC Test" : "QEMU Linux User" }
    components = {}
    components['Dejagnu'] = "Remote"
    components['GCC'] = "Remote"
    if not self.use_gnusim:
      components['QEMU Prebuilt'] = "Custom"
    components['Toolchain Prebuilt'] = "Custom"
    t.tasks['MIPS Toolchain'] = components
    return t

class GPPDejagnuTestConfig(GNUTestConfig):
  def __init__(self, use_gnusim = False):
    GNUTestConfig.__init__(self)
    self.use_gnusim = use_gnusim

  def testDefinition(self, os_part):
    t = PrefixedTestrunOptions("G++ Test")

    if os_part == "elf":
      if self.use_gnusim:
	t.tasks['MIPS Testing'] = { "G++ Test" : "GNUSIM" }
      else:
	t.tasks['MIPS Testing'] = { "G++ Test" : "QEMU System Emulator" }
    else:
      t.tasks['MIPS Testing'] = { "G++ Test" : "QEMU Linux User" }
    components = {}
    components['Dejagnu'] = "Remote"
    components['GCC'] = "Remote"
    if not self.use_gnusim:
      components['QEMU Prebuilt'] = "Custom"
    components['Toolchain Prebuilt'] = "Custom"
    t.tasks['MIPS Toolchain'] = components
    return t

class GOLDTestConfig:
  def get_p32_elf_configs(self):
    test_config = []
    t = self.testDefinition("elf")

    options = {}
    options['Manual Triple'] = "nanomips-elf"
    t.config['MIPS Prebuilt'] = options

    t.description = "R6 Bare Metal"
    test_config.append(deepcopy(t))

    return test_config

  def get_p32_linux_configs(self):
    test_config = []
    return test_config

  def testDefinition(self, os_part):
    t = PrefixedTestrunOptions("GOLD Test")

    t.tasks['MIPS Testing'] = { "GOLD Test" : "Prebuilt" }
    components = {}
    components['GOLD'] = "Remote"
    components['Toolchain Prebuilt'] = "Custom"
    t.tasks['MIPS Toolchain'] = components

    host_triple = "x86_64-pc-linux-gnu"
    config = {}
    config['Host Triple'] = host_triple
    config['Host Version'] = "4.9.4-centos5"
    t.config['MIPS Host'] = config

    return t

class GDBTestConfig:
  def get_p32_elf_configs(self):
    test_config = []
    t = self.testDefinition("elf")

    options = {}
    options['Manual Triple'] = "nanomips-elf"
    t.config['MIPS Prebuilt'] = options

    t.description = "R6 Bare Metal"
    test_config.append(deepcopy(t))

    return test_config

  def get_p32_linux_configs(self):
    test_config = []
    return test_config

  def testDefinition(self, os_part):
    t = PrefixedTestrunOptions("GDB Test")

    t.tasks['MIPS Testing'] = { "GDB Test" : "GNUSIM" }
    components = {}
    components['GDB'] = "Remote"
    components['Toolchain Prebuilt'] = "Custom"
    t.tasks['MIPS Toolchain'] = components

    return t
