from copy import deepcopy
import sys
from TestrunEditing import TestrunOptions

class GNUTestConfig:

  def __init__(self):
    self.tot = False

  def get_r6_o32_elf_configs(self):
    test_config = []
    t = self.testDefinition("elf")
  
    options = {}
    options['Manual Triple'] = "mips-img-elf"
    t.config['MIPS Prebuilt'] = options

    options = {}
    options['ABI'] = "o32"
    options['CPU'] = "mips32r6-generic"
    t.config['MIPS Test'] = options
  
    options['Endian'] = "Big"
  
    if not self.tot:
      options['CFLAGS'] = "-msoft-float -mmicromips"
      t.description = "R6 Bare Metal - BE,O32,SF,MM"
      test_config.append(deepcopy(t))
  
      options['CFLAGS'] = "-mhard-float -mmicromips"
      t.description = "R6 Bare Metal - BE,O32,HF,MM"
      test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R6 Bare Metal - BE,O32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R6 Bare Metal - BE,O32,HF"
    test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"

    if not self.tot:
      options['CFLAGS'] = "-msoft-float -mmicromips"
      t.description = "R6 Bare Metal - LE,O32,SF,MM"
      test_config.append(deepcopy(t))
  
      options['CFLAGS'] = "-mhard-float -mmicromips"
      t.description = "R6 Bare Metal - LE,O32,HF,MM"
      test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R6 Bare Metal - LE,O32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R6 Bare Metal - LE,O32,HF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float -msingle-float -fshort-double"
    t.description = "R6 Bare Metal - LE,O32,HF,S"
    test_config.append(deepcopy(t))
  
    if not self.tot:
      options['CFLAGS'] = "-march=m6201"
      t.description = "R6 Bare Metal - LE,O32,M6201"
      test_config.append(deepcopy(t))
  
      options['CFLAGS'] = "-march=m6201 -mmicromips"
      t.description = "R6 Bare Metal - LE,O32,MM,M6201"
      test_config.append(deepcopy(t))
  
    return test_config
  
  def get_r6_n32_elf_configs(self):
    test_config = []
    t = self.testDefinition("elf")

    options = {}
    options['Manual Triple'] = "mips-img-elf"
    t.config['MIPS Prebuilt'] = options
  
    options = {}
    options['ABI'] = "n32"
    options['CPU'] = "I6400"
    t.config['MIPS Test'] = options
  
    options['Endian'] = "Big"
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R6 Bare Metal - BE,N32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R6 Bare Metal - BE,N32,HF"
    test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R6 Bare Metal - LE,N32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R6 Bare Metal - LE,N32,HF"
    test_config.append(deepcopy(t))
  
    return test_config
  
  def get_r6_n64_elf_configs(self):
    test_config = []
    t = self.testDefinition("elf")

    options = {}
    options['Manual Triple'] = "mips-img-elf"
    t.config['MIPS Prebuilt'] = options
  
    options = {}
    options['ABI'] = "n64"
    options['CPU'] = "I6400"
    t.config['MIPS Test'] = options
  
    options['Endian'] = "Big"
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R6 Bare Metal - BE,N64,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R6 Bare Metal - BE,N64,HF"
    test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R6 Bare Metal - LE,N64,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R6 Bare Metal - LE,N64,HF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-march=i6400"
    t.description = "R6 Bare Metal - LE,N64,HF,I6400"
    test_config.append(deepcopy(t))
  
    if not self.tot:
      options['CFLAGS'] = "-march=p6600"
      t.description = "R6 Bare Metal - LE,N64,HF,P6600"
      test_config.append(deepcopy(t))
  
    return test_config
  
  def get_r6_o32_linux_configs(self):
    test_config = []
    t = self.testDefinition("linux")

    options = {}
    options['Manual Triple'] = "mips-img-linux-gnu"
    t.config['MIPS Prebuilt'] = options
  
    options = {}
    options['ABI'] = "o32"
    options['CPU'] = "mips32r6-generic"
    t.config['MIPS Test'] = options
  
    options['Endian'] = "Big"
  
    if not self.tot:
      options['CFLAGS'] = "-msoft-float -mmicromips"
      t.description = "R6 Linux - BE,O32,SF,MM"
      test_config.append(deepcopy(t))
  
      options['CFLAGS'] = "-mhard-float -mmicromips"
      t.description = "R6 Linux - BE,O32,HF,MM"
      test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R6 Linux - BE,O32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R6 Linux - BE,O32,HF"
    test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"
  
    if not self.tot:
      options['CFLAGS'] = "-msoft-float -mmicromips"
      t.description = "R6 Linux - LE,O32,SF,MM"
      test_config.append(deepcopy(t))
  
      options['CFLAGS'] = "-mhard-float -mmicromips"
      t.description = "R6 Linux - LE,O32,HF,MM"
      test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R6 Linux - LE,O32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R6 Linux - LE,O32,HF"
    test_config.append(deepcopy(t))
  
    return test_config
  
  def get_r6_n32_linux_configs(self):
    test_config = []
    t = self.testDefinition("linux")

    options = {}
    options['Manual Triple'] = "mips-img-linux-gnu"
    t.config['MIPS Prebuilt'] = options
  
    options = {}
    options['ABI'] = "n32"
    options['CPU'] = "I6400"
    t.config['MIPS Test'] = options
  
    options['Endian'] = "Big"
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R6 Linux - BE,N32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R6 Linux - BE,N32,HF"
    test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"
  
    if self.tot:
      options['CFLAGS'] = "-msoft-float"
      t.description = "R6 Linux - LE,N32,SF"
      test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R6 Linux - LE,N32,HF"
    test_config.append(deepcopy(t))
  
    return test_config
  
  def get_r6_n64_linux_configs(self):
    test_config = []
    t = self.testDefinition("linux")

    options = {}
    options['Manual Triple'] = "mips-img-linux-gnu"
    t.config['MIPS Prebuilt'] = options
  
    options = {}
    options['ABI'] = "n64"
    options['CPU'] = "I6400"
    t.config['MIPS Test'] = options
  
    options['Endian'] = "Big"
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R6 Linux - BE,N64,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R6 Linux - BE,N64,HF"
    test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"
  
    if self.tot:
      options['CFLAGS'] = "-msoft-float"
      t.description = "R6 Linux - LE,N64,SF"
      test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R6 Linux - LE,N64,HF"
    test_config.append(deepcopy(t))
  
    return test_config
  
  def get_r2_o32_elf_configs(self):
    test_config = []
    t = self.testDefinition("elf")

    options = {}
    options['Manual Triple'] = "mips-mti-elf"
    t.config['MIPS Prebuilt'] = options
  
    options = {}
    options['ABI'] = "o32"
    options['CPU'] = "P5600"
    t.config['MIPS Test'] = options
  
    options['Endian'] = "Big"

    options['CFLAGS'] = "-msoft-float -mmicromips"
    t.description = "R2 Bare Metal - BE,O32,SF,MM"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float -mmicromips"
    t.description = "R2 Bare Metal - BE,O32,HF,MM"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R2 Bare Metal - BE,O32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R2 Bare Metal - BE,O32,HF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float -mnan=2008"
    t.description = "R2 Bare Metal - BE,O32,HF,N8"
    test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"
  
    options['CFLAGS'] = "-msoft-float -mmicromips"
    t.description = "R2 Bare Metal - LE,O32,SF,MM"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float -mmicromips"
    t.description = "R2 Bare Metal - LE,O32,HF,MM"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R2 Bare Metal - LE,O32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R2 Bare Metal - LE,O32,HF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float -mnan=2008"
    t.description = "R2 Bare Metal - LE,O32,HF,N8"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-march=p5600"
    t.description = "R2 Bare Metal - LE,O32,P5600"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-march=m5101"
    t.description = "R2 Bare Metal - LE,O32,M5101"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-march=m5100"
    t.description = "R2 Bare Metal - LE,O32,M5100"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-march=m5100 -mmicromips"
    t.description = "R2 Bare Metal - LE,O32,MM,M5100"
    test_config.append(deepcopy(t))
  
    return test_config
  
  def get_r2_n32_elf_configs(self):
    test_config = []
    t = self.testDefinition("elf")

    options = {}
    options['Manual Triple'] = "mips-mti-elf"
    t.config['MIPS Prebuilt'] = options
  
    options = {}
    options['ABI'] = "n32"
    options['CPU'] = "MIPS64R2-generic"
    t.config['MIPS Test'] = options
  
    options['Endian'] = "Big"
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R2 Bare Metal - BE,N32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R2 Bare Metal - BE,N32,HF"
    test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R2 Bare Metal - LE,N32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R2 Bare Metal - LE,N32,HF"
    test_config.append(deepcopy(t))
  
    return test_config
  
  def get_r2_n64_elf_configs(self):
    test_config = []
    t = self.testDefinition("elf")

    options = {}
    options['Manual Triple'] = "mips-mti-elf"
    t.config['MIPS Prebuilt'] = options
  
    options = {}
    options['ABI'] = "n64"
    options['CPU'] = "MIPS64R2-generic"
    t.config['MIPS Test'] = options
  
    options['Endian'] = "Big"
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R2 Bare Metal - BE,N64,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R2 Bare Metal - BE,N64,HF"
    test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R2 Bare Metal - LE,N64,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R2 Bare Metal - LE,N64,HF"
    test_config.append(deepcopy(t))
  
    return test_config
  
  def get_r2_o32_linux_configs(self):
    test_config = []
    t = self.testDefinition("linux")

    options = {}
    options['Manual Triple'] = "mips-mti-linux-gnu"
    t.config['MIPS Prebuilt'] = options
  
    options = {}
    options['ABI'] = "o32"
    options['CPU'] = "P5600"
    t.config['MIPS Test'] = options
  
    options['Endian'] = "Big"
  
    if self.tot:
      options['CFLAGS'] = "-msoft-float -mmicromips"
      t.description = "R2 Linux - BE,O32,SF,MM"
      test_config.append(deepcopy(t))
  
      options['CFLAGS'] = "-mhard-float -mmicromips -mnan=2008"
      t.description = "R2 Linux - BE,O32,HF,MM,N8"
      test_config.append(deepcopy(t))

    options['CFLAGS'] = "-msoft-float"
    t.description = "R2 Linux - BE,O32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float -mnan=2008"
    t.description = "R2 Linux - BE,O32,HF,N8"
    test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"
  
    options['CFLAGS'] = "-msoft-float -mmicromips"
    t.description = "R2 Linux - LE,O32,SF,MM"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float -mmicromips -mnan=2008"
    t.description = "R2 Linux - LE,O32,HF,MM,N8"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-msoft-float"
    t.description = "R2 Linux - LE,O32,SF"
    test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float -mnan=2008"
    t.description = "R2 Linux - LE,O32,HF,N8"
    test_config.append(deepcopy(t))
  
    return test_config
  
  def get_r2_n32_linux_configs(self):
    test_config = []
    t = self.testDefinition("linux")

    options = {}
    options['Manual Triple'] = "mips-mti-linux-gnu"
    t.config['MIPS Prebuilt'] = options
  
    options = {}
    options['ABI'] = "n32"
    options['CPU'] = "MIPS64R2-generic"
    t.config['MIPS Test'] = options
  
    options['Endian'] = "Big"
  
    if self.tot:
      options['CFLAGS'] = "-msoft-float"
      t.description = "R2 Linux - BE,N32,SF"
      test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R2 Linux - BE,N32,HF"
    test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"
  
    if self.tot:
      options['CFLAGS'] = "-msoft-float"
      t.description = "R2 Linux - LE,N32,SF"
      test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R2 Linux - LE,N32,HF"
    test_config.append(deepcopy(t))
  
    return test_config
  
  def get_r2_n64_linux_configs(self):
    test_config = []
    t = self.testDefinition("linux")

    options = {}
    options['Manual Triple'] = "mips-mti-linux-gnu"
    t.config['MIPS Prebuilt'] = options
  
    options = {}
    options['ABI'] = "n64"
    options['CPU'] = "MIPS64R2-generic"
    t.config['MIPS Test'] = options
  
    options['Endian'] = "Big"
  
    if self.tot:
      options['CFLAGS'] = "-msoft-float"
      t.description = "R2 Linux - BE,N64,SF"
      test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R2 Linux - BE,N64,HF"
    test_config.append(deepcopy(t))
  
    options['Endian'] = "Little"
  
    if self.tot:
      options['CFLAGS'] = "-msoft-float"
      t.description = "R2 Linux - LE,N64,SF"
      test_config.append(deepcopy(t))
  
    options['CFLAGS'] = "-mhard-float"
    t.description = "R2 Linux - LE,N64,HF"
    test_config.append(deepcopy(t))
  
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
      components['QEMU Prebuilt'] = "From Toolchain"
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
      components['QEMU Prebuilt'] = "From Toolchain"
    components['Toolchain Prebuilt'] = "Custom"
    t.tasks['MIPS Toolchain'] = components
    return t

class GASTestConfig:
  def get_elf_configs(self):
    test_config = []
    t = self.testDefinition("elf")
    options = {}
    options['Manual Triple'] = "mips-mti-elf"
    t.config['MIPS Prebuilt'] = options
    t.description = "MTI Bare Metal"
    test_config.append(deepcopy(t))
    return test_config

  def get_linux_configs(self):
    test_config = []
    t = self.testDefinition("linux")
    options = {}
    options['Manual Triple'] = "mips-mti-linux-gnu"
    t.config['MIPS Prebuilt'] = options
    t.description = "MTI Linux"
    test_config.append(deepcopy(t))
    return test_config

  def testDefinition(self, os_part):
    t = PrefixedTestrunOptions("GAS Test")
    t.tasks['MIPS Testing'] = { "GAS Test" : "Prebuilt" }
    components = {}
    components['Binutils'] = "Remote"
    components['Toolchain Prebuilt'] = "Custom"
    t.tasks['MIPS Toolchain'] = components
    return t

class LDTestConfig(GASTestConfig):
  def testDefinition(self, os_part):
    t = PrefixedTestrunOptions("GNU LD Test")
    t.tasks['MIPS Testing'] = { "GNU LD Test" : "Prebuilt" }
    components = {}
    components['Binutils'] = "Remote"
    components['Toolchain Prebuilt'] = "Custom"
    t.tasks['MIPS Toolchain'] = components
    return t
