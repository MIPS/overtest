import os
from Action import Action
from Config import CONFIG
from OvertestExceptions import ConfigException
import re
import glob
import time
import random

# Toolchain Build

class A117819(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117819
    self.name = "Toolchain Build"

  def _addConfig(self, config, option, value):
    if value != "":
      config.append(option % value)

  # Execute the action.
  def run(self):
    if self.concurrency == 1:
      if hasattr(CONFIG,'cores'):
        self.concurrency = CONFIG.cores
      else:
        self.concurrency = 12

    if not os.path.exists (os.path.join(self.getWorkPath(), "mips_tool_chain")):
      # Execute a command overriding some environment variables
      for i in range(30):
        result = self.execute(command=[CONFIG.git, "clone",
                                       "--reference=%s/mips_tool_chain.git" % CONFIG.gitref,
                                       "--branch=master",
                                       "%s/mips_tool_chain.git" % CONFIG.gitremote,
                                       "mips_tool_chain"])
        if result == 0:
          break
        else:
          time.sleep(random.randint(1,30))

      if result != 0:
        self.error("Unable to clone repository")

    # Now construct the work area
    result = self.execute(command=["build_scripts/make_workarea %s %s" % (self.getWorkPath(), CONFIG.gitremote)],
			  workdir=os.path.join(self.getWorkPath(), "mips_tool_chain"),
			  shell=True)
    if result != 0:
      self.error("Unable to make work area")

    result = self.execute(command=[CONFIG.git, "checkout", "master"],
			  workdir=os.path.join(self.getWorkPath(), "src", "mips_tool_chain"))

    if result != 0:
      self.error("Unable to change branch")

    result = self.execute(workdir=os.path.join(self.getWorkPath(), "src", "mips_tool_chain"),
	                  command=[CONFIG.git, "rev-parse", "HEAD"])
    if result == 0:
      self.config.setVariable("Toolchain Build rev", self.fetchOutput().strip())

    try:
      arch = self.config.getVariable("Architecture")
    except ConfigException, e:
      arch = "mips"

    if "Generic" in self.version:
      endian = self.config.getVariable("Endian")
      if endian != "":
	endian = ""
        if arch == "mips":
	  if endian != "big":
	    endian = "el"
	else:
	  if endian == "big":
	    endian = "eb"

      bitsize = self.config.getVariable("Arch 64")
      if bitsize != "":
	bitsize = "64"
      else:
	bitsize = ""
      vendor = ""
    else:
      vendor = self.config.getVariable("Vendor")
      if vendor != "":
	vendor = "%s-" % vendor
      bitsize = ""
      endian = ""

    if self.version.startswith("Linux"):
      if "musl" in self.version:
	target = "%s%s%s-%slinux-musl" % (arch, bitsize, endian, vendor)
      else:
	target = "%s%s%s-%slinux-gnu" % (arch, bitsize, endian, vendor)
    else:
      target = "%s%s%s-%self" % (arch, bitsize, endian, vendor)

    extra_config = self.config.getVariable("Extra Config")

    install = os.path.join(self.getSharedPath(), "install-%s" % target)
    installtgz = None
    manual_install = self.config.getVariable("Install Root")
    if manual_install != "":
      if manual_install.endswith(".tgz") or manual_install.endswith(".tar.gz"):
	installtgz = manual_install
	if re.match("^[0-9]{4}\.[0-9]{2}-[0-9]{2}$",
		    self.config.getVariable("Release Version")) is not None:
	  foldername = os.path.join(target, self.config.getVariable("Release Version"))
	elif re.match("^[0-9]{4}\.[0-9]{2}-[0-9]{2}-trial-[0-9]{1,2}$",
		    self.config.getVariable("Release Version")) is not None:
	  foldername = os.path.join(target, self.config.getVariable("Release Version"))
	elif re.match("^[0-9]{4}\.[0-9]{2}-[0-9]{2}-alpha-[0-9]{1,2}$",
		    self.config.getVariable("Release Version")) is not None:
	  foldername = os.path.join(target, self.config.getVariable("Release Version"))
	elif re.match("^[0-9]{4}\.[0-9]{2}-[0-9]{2}-beta-[0-9]{1,2}$",
		    self.config.getVariable("Release Version")) is not None:
	  foldername = os.path.join(target, self.config.getVariable("Release Version"))
	elif installtgz.endswith(".tar.gz"):
	  foldername = os.path.basename(installtgz)[0:-7]
	elif installtgz.endswith(".tgz"):
	  foldername = os.path.basename(installtgz)[0:-4]
	else:
	  foldername = "install-%s" % target
	install = os.path.join(self.getSharedPath(), foldername)
      else:
	install = manual_install
    hostinstall = os.path.join(self.getSharedPath(), "hostinstall-%s" % target)
    buildinstall = os.path.join(self.getSharedPath(), "buildinstall-%s" % target)

    build = os.path.join(self.getWorkPath(), "obj-%s" % target)

    # Set up the location of the newly built tools
    host_path = ":".join([os.path.join(install, "bin"),
			  os.path.join(buildinstall, "bin"),
                          os.path.join(hostinstall, "bin")])

    # Add in the path of any host compiler specified
    try:
      host_triple = self.config.getVariable("Host Triple")
      if host_triple != "":
	host_version = self.config.getVariable("Host Version")
	host_bin = "/projects/mipssw/toolchains/%s/%s/bin" % (host_triple, host_version)
	host_path = ":".join([host_path, host_bin])
    except ConfigException, e:
      host_triple = ""
      pass

    # Add in the reference compiler for canadian cross builds
    if "Canadian Cross" in self.version:
      # A canadian cross consumes a prebuilt toolchain
      reference_root = self.config.getVariable("Toolchain Root")
      host_path = ":".join([os.path.join(reference_root, "bin"),host_path])
      if os.path.exists(os.path.join(reference_root, "python-root")):
        host_path = ":".join([os.path.join(reference_root, "python-root", "bin"),host_path])
      # It also just steals all target files from the reference to
      # save build time and avoid unneccessary differences in target
      # objects
      cmd = ["b/copy_cross_target %s %s %s" % (target, reference_root, install)]
      if self.execute(command=cmd, shell=True) != 0:
        self.error("Failed to copy reference target files")
    else:
      # A canadian cross cannot be used to build anything further but
      # a normal build is usable by testsuites
      self.config.setVariable("Triple", target)
      self.config.setVariable("Toolchain Root", install)

    # Unpack the build/host support libraries source
    options = ["--git_home=%s" % CONFIG.gitremote,
	       "--prefix=/none",
	       "--jobs=%d" % self.concurrency]


    build_qemu = False
    if self.testrun.getVersion("QEMU") != None:
      build_qemu = True

    components = ["expat", "termcap", "ncurses", "texinfo", "openssl"]
    opt_components = []
    if self.version.startswith("Linux"):
      opt_components = ["make", "bison"]

    if build_qemu:
      components.extend(["zlib", "pixman", "libffi", "glib"])
      components.extend(["libiconv", "gettext"])

    source = {}
    for component in components:
      pkg = glob.glob(os.path.join(self.testrun.getSharedPath("Packages"),
				   "packages", "%s*" % component))
      if len(pkg) != 1:
        self.error("Could not locate %s package" % component)
      source[component] = "--src=%s:%s" % (component, pkg[0])
      options.append(source[component])

    for component in opt_components:
      pkg = glob.glob(os.path.join(self.testrun.getSharedPath("Packages"),
				   "packages", "%s*" % component))
      if len(pkg) != 1:
        opt_components.remove(component)
      else:
        source[component] = "--src=%s:%s" % (component, pkg[0])
        options.append(source[component])

    cmd = ["b/build_toolchain", "update"]
    cmd.extend(options)

    if self.execute(command=[" ".join(cmd + components)], shell=True) != 0:
      self.error("Failed to unpack build/host components")

    # Build 'build' support libraries for all tools
    options = ["--git_home=%s" % CONFIG.gitremote,
	       "--prefix=%s" % buildinstall,
	       "--build=%s" % build,
	       "--jobs=%d" % self.concurrency]
    components = ["texinfo"]

    cmd = ["b/build_toolchain", "build"]
    cmd.extend(options)
    for component in components:
      if self.execute(command=[" ".join(cmd + [source[component], component])], shell=True) != 0:
	self.error("Failed to build %s" % component)

    # Unpack host support libraries source
    options = ["--git_home=%s" % CONFIG.gitremote,
	       "--prefix=%s" % hostinstall,
	       "--build=%s" % build,
	       "--jobs=%d" % self.concurrency]

    # Set the host tools if specified
    if host_triple != "":
      options.append("--host=%s" % host_triple)
      options.append("--path=%s" % host_path)

    components = ["expat", "termcap", "ncurses", "openssl"]
    components.extend (opt_components)
    if build_qemu:
      components.extend(["zlib", "pixman", "libffi"])
      components.extend(["libiconv", "gettext", "glib"])

    # Build host support libraries for GDB
    cmd = ["b/build_toolchain", "build"]
    cmd.extend(options)
    cmd.append("--hostlibs=%s" % hostinstall)
    for component in components:
      if self.execute(command=[" ".join(cmd + [source[component], component])], shell=True) != 0:
	self.error("Failed to build %s" % component)

    # Prepare special build options for python
    if self.testrun.getVersion("Python") != None and "mingw" not in host_triple:
      options = ["--git_home=%s" % CONFIG.gitremote,
	         "--prefix=%s/python-root" % install,
	         "--build=%s" % build,
                 "--host=%s" % host_triple,
                 "--path=%s" % host_path,
	         "--jobs=%d" % self.concurrency]
      python = os.path.join(self.testrun.getSharedPath("Python"), "python")
      options.append("--src=python:%s" % python)
      if "mingw" in host_triple:
        options.append("--build_triple=x86_64-pc-linux-gnu")
      else:
        options.append("--build_triple=%s" % host_triple)
      cmd = ["b/build_toolchain", "build"]
      cmd.extend(options)
      cmd.append("--hostlibs=%s" % hostinstall)
      if self.execute(command=[" ".join(cmd + ["python"])], shell=True) != 0:
        self.error("Failed to build Python")

    # Prepare for main tools build
    options = ["--path=%s" % host_path,
	       "--git_home=%s" % CONFIG.gitremote,
	       "--build=%s" % build,
	       "--prefix=%s" % install,
	       "--target=%s" % target,
	       "--jobs=%d" % self.concurrency]

    # Set the host tools if specified
    if host_triple != "":
      options.append("--host=%s" % host_triple)
      # For linux hosted builds we expect the newly built tools to execute on
      # the current distro as the C library used should be older than the
      # native one.  We do this by forcing the build and host to match.
      if "pc-linux-gnu" in host_triple:
        options.append("--build_triple=%s" % host_triple)

    # Gather the location of all the packages
    mpc = glob.glob(os.path.join(self.testrun.getSharedPath("Packages"), "packages", "mpc*"))
    if len(mpc) != 1:
      self.error("Could not locate MPC package")
    options.append("--src=mpc:%s" % mpc[0])
    mpfr = glob.glob(os.path.join(self.testrun.getSharedPath("Packages"), "packages", "mpfr*"))
    if len(mpfr) != 1:
      self.error("Could not locate MPFR package")
    options.append("--src=mpfr:%s" % mpfr[0])
    gmp = glob.glob(os.path.join(self.testrun.getSharedPath("Packages"), "packages", "gmp*"))
    if len(gmp) != 1:
      self.error("Could not locate GMP package")
    options.append("--src=gmp:%s" % gmp[0])

    if self.version.startswith("Linux"):
      if arch == "nanomips":
        linux = os.path.join(self.testrun.getSharedPath("Packages"), "packages", "linux-nda.tar.gz")
      else:
	linux = os.path.join(self.testrun.getSharedPath("Packages"), "packages", "linux-4.9.189.tar.bz2")
      options.append("--src=linux:%s" % linux)
      sysroot = os.path.join(install, "sysroot")
      options.append("--sysroot=%s" % sysroot)
      if not "Canadian Cross" in self.version:
        if "musl" in self.version:
	  musl = os.path.join(self.testrun.getSharedPath("Musl"), "musl")
	  options.append("--src=musl:%s" % musl)
	else:
	  glibc = os.path.join(self.testrun.getSharedPath("Glibc"), "glibc")
	  options.append("--src=glibc:%s" % glibc)
	  if self.version != "Linux.29.06.15":
	    uclibc = os.path.join(self.testrun.getSharedPath("uClibc"), "uclibc")
	    options.append("--src=uclibc:%s" % uclibc)
    elif not "Canadian Cross" in self.version:
      newlib = os.path.join(self.testrun.getSharedPath("Newlib"), "newlib")
      options.append("--src=newlib:%s" % newlib)
      if self.testrun.getVersion("SmallClib") != None:
	smallclib = os.path.join(self.testrun.getSharedPath("SmallClib"), "smallclib")
	options.append("--src=smallclib:%s" % smallclib)

    binutils = os.path.join(self.testrun.getSharedPath("Binutils"), "binutils")
    options.append("--src=binutils:%s" % binutils)
    if self.testrun.getVersion("GOLD") != None:
      gold = os.path.join(self.testrun.getSharedPath("GOLD"), "gold")
      options.append("--src=gold:%s" % gold)
    gcc = os.path.join(self.testrun.getSharedPath("GCC"), "gcc")
    options.append("--src=gcc:%s" % gcc)
    gdb = os.path.join(self.testrun.getSharedPath("GDB"), "gdb")
    options.append("--src=gdb:%s" % gdb)
    options.append("--src=gdb-py:%s" % gdb)
    if build_qemu:
      qemu = os.path.join(self.testrun.getSharedPath("QEMU"), "qemu")
      options.append("--src=qemu:%s" % qemu)

    # Determine if this is a new style build where newlib is built as part of
    # the GCC build
    new_elf_build = os.path.exists(os.path.join(gcc, "gcc", "config", "mips", "ml-mti-elf"))
   
    # Extract support libraries for GCC
    cmd = ["b/build_toolchain", "update"]
    cmd.extend(options)

    if self.execute(command=[" ".join(cmd + ["gmp", "mpfr", "mpc"])], shell=True) != 0:
      self.error("Failed to unpack gmp, mpfr and mpc")

    # Set the support url and package names
    if not "Generic" in self.version:
      if "Linux" in self.version:
	os_string = "Linux"
      else:
	os_string = "Bare Metal"
      version_name = self.config.getVariable("Release Version")
      version_arch = "MIPS"
      if arch == "nanomips":
        version_arch = "nanoMIPS"
      vendor_string = self.config.getVariable("Vendor").upper()
      if vendor_string != "":
	vendor_string += " "
      version_string = "Codescape GNU Tools %s for %s %s%s" % \
		       (version_name, version_arch, vendor_string, os_string)
    else:
      version_string = self.config.getVariable("Release Version")

    options.append("--with-bugurl=http://mips.com/mips-sdk-support/")
    options.append("--with-pkgversion=\"%s\"" % version_string)
    options.append("--buildlibs=%s" % buildinstall)

    # Build binutils
    cmd = ["b/build_toolchain", "build"]
    cmd.extend(options)
    if self.execute(command=[" ".join(cmd + ["binutils"])], shell=True) != 0:
      self.error("Failed to build binutils")

    if self.testrun.getVersion("GOLD") != None:
      if self.execute(command=[" ".join(cmd + ["gold"])], shell=True) != 0:
	self.error("Failed to build gold")

    # Get GCC configure options
    extra_gcc_config = []
    if "Generic" in self.version:
      self._addConfig(extra_gcc_config, "--with-arch-32=%s",
		      self.config.getVariable("Arch 32"))
      self._addConfig(extra_gcc_config, "--with-arch-64=%s",
		      self.config.getVariable("Arch 64"))
      self._addConfig(extra_gcc_config, "--with-float=%s",
		      self.config.getVariable("Float"))
      self._addConfig(extra_gcc_config, "--with-fpu=%s",
		      self.config.getVariable("FPU"))
      self._addConfig(extra_gcc_config, "--with-nan=%s",
		      self.config.getVariable("NaN"))
      self._addConfig(extra_gcc_config, "--with-fp-32=%s",
		      self.config.getVariable("FP"))
      self._addConfig(extra_gcc_config, "--with-odd-spreg-32=%s",
		      self.config.getVariable("Odd SP Reg"))

    extra_gcc_config.append(extra_config.replace("$SRC_DIR",gcc))
    extra_gcc_config = "--extra_config_opts=\"%s\"" % " ".join(extra_gcc_config)
    if self.config.getVariable("Disable Multilib"):
      extra_gcc_config = "%s --disable-multilib" % extra_gcc_config

    # A canadian cross does not need to build libraries as they can be copied
    # from the reference tools
    if "Canadian Cross" in self.version:
      gcc_all_target = "all-host"
      gcc_install_target = "install-host"
    else:
      # set default targets
      gcc_all_target = ""
      gcc_install_target = ""
      if self.version.startswith("Linux") or not new_elf_build:
	if self.execute(command=[" ".join(cmd + [extra_gcc_config,
						 "--make_target_install=skip",
						 "initial_gcc"])], shell=True) != 0:
	  self.error("Failed to build initial_gcc")
	if self.execute(command=[" ".join(cmd + [extra_gcc_config,
						 "--make_target_all=skip",
						 "--jobs=1",
						 "initial_gcc"])], shell=True) != 0:
	  self.error("Failed to install initial_gcc")

      if self.version.startswith("Linux"):
	if self.execute(command=[" ".join(cmd + ["linux_headers"])], shell=True) != 0:
	  self.error("Failed to build linux_headers")
        extra_glibc_config = "--hostlibs=%s" % hostinstall
	if "Generic" in self.version:
	  if self.config.getVariable("Float") == "soft":
	    extra_glibc_config = "--extra_config_opts=\"--without-fp\""
	if self.execute(command=[" ".join(cmd + [extra_glibc_config, "sysroot"])], shell=True) != 0:
	  self.error("Failed to build sysroot")
      elif not new_elf_build:
	if self.execute(command=[" ".join(cmd + ["newlib"])], shell=True) != 0:
	  self.error("Failed to build newlib")

    # Split the build from the install as parallel install can fail
    if self.execute(command=[" ".join(cmd + [extra_gcc_config,
	                                     "--make_target_all='%s'" % gcc_all_target,
	                                     "--make_target_install=skip",
                                             "gcc"])], shell=True) != 0:
      self.error("Failed to build gcc")

    if self.execute(command=[" ".join(cmd + [extra_gcc_config,
	                                     "--make_target_all=skip",
	                                     "--make_target_install='%s'" % gcc_install_target,
					     "--jobs=1",
                                             "gcc"])], shell=True) != 0:
      self.error("Failed to install gcc")

    if not "Canadian Cross" in self.version and new_elf_build \
       and self.version.startswith("Bare Metal") \
       and self.testrun.getVersion("SmallClib") != None:
      env = {}
      env['PATH'] = CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.cmake), os.environ['PATH']])
      if self.execute(command=[" ".join(cmd + ["smallclib"])], shell=True, env=env) != 0:
	self.error("Failed to build smallclib")

    # Build GDB with the newly built host libexpat
    extra_host = "--hostlibs=%s" % hostinstall
    if self.execute(command=[" ".join(cmd + [extra_host, "gdb"])], shell=True) != 0:
      self.error("Failed to build gdb")

    if self.testrun.getVersion("Python") != None and "mingw" not in host_triple:
      if self.execute(command=[" ".join(cmd + [extra_host, "gdb-py"])], shell=True) != 0:
        self.error("Failed to build gdb-py")

    if build_qemu:
      if self.execute(command=[" ".join(cmd + [extra_host, "qemu"])], shell=True) != 0:
	self.error("Failed to build qemu")

    # Set the permissions to match release requirements
    if self.execute(command=["chmod", "-R", "o+rX", install]) != 0:
      self.error("Failed to set permissions")

    self.execute(command=["strip -d bin/* %s/bin/* libexec/gcc/%s/*/* python-root/bin/*" % (target, target)],
		 workdir=install,
		 shell=True)

    # Finalise the build
    if installtgz != None:
      self.createDirectory(os.path.dirname(installtgz))
      cmd=["tar"]
      if "mingw" in host_triple:
        cmd.extend(["--dereference", "--hard-dereference"])

      if self.execute(command = (cmd + ["--owner=0", "--group=0",
                                         "-pczf", installtgz,
                                         foldername]),
		      workdir=self.getSharedPath()) != 0:
        self.error("Failed to tar up toolchain")

    return self.success()
