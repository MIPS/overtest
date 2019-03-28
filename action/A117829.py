import os
from Action import Action
from Config import CONFIG
import glob

# Native Toolchain Build

class A117829(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117829
    self.name = "Native Toolchain Build"

  def _addConfig(self, config, option, value):
    if value != "":
      config.append(option % value)

  # Execute the action.
  def run(self):
    # Execute a command overriding some environment variables
    for i in range(30):
      result = self.execute(command=[CONFIG.git, "clone",
                                     "--reference=/projects/mipssw/git/mips_tool_chain.git",
                                     "--branch=master",
                                     "git://mipssw-mgmt.ba.imgtec.org/mips_tool_chain.git",
                                     "mips_tool_chain"])
      if result == 0:
	break
      else:
	time.sleep(random.randint(1,30))

    if result != 0:
      self.error("Unable to clone repository")

    # Now construct the work area
    result = self.execute(command=["build_scripts/make_workarea %s %s" % (self.getWorkPath(), "git://mipssw-mgmt.ba.imgtec.org")],
			  workdir=os.path.join(self.getWorkPath(), "mips_tool_chain"),
			  shell=True)
    if result != 0:
      self.error("Unable to make work area")

    result = self.execute(command=[CONFIG.git, "checkout", "master"],
			  workdir=os.path.join(self.getWorkPath(), "src", "mips_tool_chain"))

    if result != 0:
      self.error("Unable to change branch")

    variant = self.config.getVariable("Native Variant")
    installroot = self.config.getVariable("Native Install Root")

    cross_target = self.config.getVariable("Triple")
    cross_install = self.config.getVariable("Toolchain Root")

    arch = variant.split(" ")[0].lower()
    configure_opts = ["--with-arch=%s" % arch]
    sysroot_flags = ["-march=%s" % arch]

    bitsize = ""
    abi = ""
    abidir = ""
    if "O32" in variant:
      configure_opts.append("--with-abi=32")
      sysroot_flags.append("-mabi=32")
      abi = "32"
      abidir = "lib"
    elif "N32" in variant:
      bitsize = "64"
      configure_opts.append("--with-abi=n32")
      sysroot_flags.append("-mabi=n32")
      abi = "n32"
      abidir = "lib32"
    elif "N64" in variant:
      bitsize = "64"
      configure_opts.append("--with-abi=64")
      sysroot_flags.append("-mabi=64")
      abi = "64"
      abidir = "lib64"

    if "HF" in variant:
      configure_opts.append("--with-float=hard")
      sysroot_flags.append("-mhard-float")
    elif "SF" in variant:
      configure_opts.append("--with-float=soft")
      sysroot_flags.append("-msoft-float")

    if "N8" in variant:
      configure_opts.append("--with-nan=2008")
      sysroot_flags.append("-mnan=2008")

    if "LE" in variant:
      endian = "el"
      sysroot_flags.append("-EL")
    else:
      endian = ""
      sysroot_flags.append("-EB")

    target = "mips%s%s-linux-gnu" % (bitsize, endian)

    if self.execute(command=[os.path.join(cross_install, "bin", "%s-gcc" % cross_target),
                             "-print-sysroot"] + sysroot_flags) != 0:
      self.error("Unable to determine sysroot location")
    cross_sysroot = self.fetchOutput().strip()

    installname = "%s-%s" % (os.path.basename(cross_sysroot), abi)

    extra_config = self.config.getVariable("Extra Config")

    install = os.path.join(self.getSharedPath(), installname)
    obj = os.path.join(self.getSharedPath(), "obj-%s" % installname)
    buildinstall = os.path.join(self.getSharedPath(), "buildinstall")
    objbuild = os.path.join(self.getSharedPath(), "obj-build")
    installref = "%s-ref" % install
    objref = "%s-ref" % obj

    # Set up the location of the newly built tools
    host_path = ":".join([os.path.join(installref, "bin"),
                          os.path.join(buildinstall, "bin")])

    if self.execute(command=["b/make_buildroot_sysroot %s %s %s" %
                             (install, cross_sysroot, abidir)],
		    shell=True) != 0:
      self.error("Failed to create buildroot sysroot")

    source = {}
    # Gather the location of all the packages
    for pkg in ["mpc", "mpfr", "gmp", "termcap", "ncurses", "expat", "texinfo"]:
      location = glob.glob(os.path.join(self.testrun.getSharedPath("Packages"),
	                                "packages", "%s*" % pkg))
      if len(location) != 1:
        self.error("Could not locate %s package" % pkg)
      source[pkg] = "--src=%s:%s" % (pkg, location[0])

    binutils = os.path.join(self.testrun.getSharedPath("Binutils"), "binutils")
    source["binutils"] = "--src=binutils:%s" % binutils
    gcc = os.path.join(self.testrun.getSharedPath("GCC"), "gcc")
    source["gcc"] = "--src=gcc:%s" % gcc
    gdb = os.path.join(self.testrun.getSharedPath("GDB"), "gdb")
    source["gdb"] = "--src=gdb:%s" % gdb

    options = ["--path=%s" % host_path,
	       "--git_home=git://mipssw-mgmt.ba.imgtec.org",
	       "--build=%s" % objbuild,
	       "--prefix=%s" % buildinstall,
	       "--jobs=%d" % self.concurrency]

    cmd = ["b/build_toolchain", "update"]
    cmd.extend(options)
    for src in ["gmp", "mpfr", "mpc", "termcap", "ncurses", "expat", "texinfo"]:
      cmd.append(source[src])

    if self.execute(command=[" ".join(cmd + ["gmp", "mpfr", "mpc",
                                             "termcap", "ncurses", "expat", "texinfo"])],
		    shell=True) != 0:
      self.error("Failed to unpack components")

    cmd = ["b/build_toolchain", "build"]
    cmd.extend(options)

    if self.execute(command=[" ".join(cmd + [source["texinfo"],
                                             "texinfo"])], shell=True) != 0:
      self.error("Failed to build texinfo")

    options = ["--path=%s" % host_path,
	       "--git_home=git://mipssw-mgmt.ba.imgtec.org",
	       "--build=%s" % objref,
	       "--prefix=%s" % installref,
	       "--sysroot=%s" % install,
	       "--disable-multilib",
	       "--target=%s" % target,
	       "--jobs=%d" % self.concurrency]

    cmd = ["b/build_toolchain", "build"]
    cmd.extend(options)
    if self.execute(command=[" ".join(cmd + [source["binutils"],
                                             "binutils"])], shell=True) != 0:
      self.error("Failed to build reference binutils")

    # Get GCC configure options
    extra_gcc_config = "--extra_config_opts=\"%s\"" % " ".join(configure_opts)

    if self.execute(command=[" ".join(cmd + [extra_gcc_config,
                                             source["gcc"],
	                                     "--make_target_install=skip",
					     "gcc"])], shell=True) != 0:
      self.error("Failed to build reference gcc")
    if self.execute(command=[" ".join(cmd + [extra_gcc_config,
                                             source["gcc"],
	                                     "--make_target_all=skip",
					     "gcc"])], shell=True) != 0:
      self.error("Failed to install reference gcc")

    options = ["--path=%s" % host_path,
	       "--git_home=git://mipssw-mgmt.ba.imgtec.org",
	       "--build=%s" % obj,
	       "--prefix=%s" % os.path.join(install, "usr"),
	       "--sysroot=%s" % install,
	       "--target=%s" % target,
	       "--host=%s" % target,
	       "--hostlibs=%s" % install,
    	       "--buildlibs=%s" % buildinstall,
	       "--jobs=%d" % self.concurrency]

#    version_name = self.config.getVariable("Release Version")
#
#    vendor = "UNKNOWN"
#    if arch.endswith("R2"):
#      vendor = "MTI"
#    elif arch.endswith("R6"):
#      vendor = "IMG"
#
#    version_string = "Codescape GNU Tools %s for MIPS %s Linux" % \
#                       (version_name, vendor)
#    options.append("--with-bugurl=http://imgtec.com/mips-sdk-support/")
#    options.append("--with-pkgversion=\"%s\"" % version_string)

    cmd = ["b/build_toolchain", "build"]
    cmd.extend(options)

    if self.execute(command=[" ".join(cmd + [source["binutils"],
                                             "binutils"])], shell=True) != 0:
      self.error("Failed to build native binutils")

    if self.execute(command=[" ".join(cmd + [extra_gcc_config,
                                             source["gcc"],
	                                     "--make_target_install=skip",
                                             "gcc"])], shell=True) != 0:
      self.error("Failed to build native gcc")
    if self.execute(command=[" ".join(cmd + [extra_gcc_config,
                                             source["gcc"],
	                                     "--make_target_all=skip",
                                             "gcc"])], shell=True) != 0:
      self.error("Failed to install native gcc")

    if self.execute(command=[" ".join(cmd + [source["termcap"],
	                                     "termcap"])], shell=True) != 0:
      self.error("Failed to build native termcap")

    if self.execute(command=[" ".join(cmd + [source["ncurses"],
                                             "ncurses"])], shell=True) != 0:
      self.error("Failed to build native ncurses")

    if self.execute(command=[" ".join(cmd + [source["expat"],
                                             "expat"])], shell=True) != 0:
      self.error("Failed to build native expat")

    if self.execute(command=[" ".join(cmd + [source["gdb"],
                                             "gdb"])], shell=True) != 0:
      self.error("Failed to build native gdb")

    if installroot != "":
      try:
	if not os.path.exists(installroot):
	  os.makedirs(installroot)
      except OSError, e:
	self.error("Failed to create install area: %s" % e)
      if self.execute(command=["tar", "-czf",
                               os.path.join(installroot, "%s.tgz" % installname),
	                       installname],
		      workdir=self.getSharedPath()) != 0:
        self.error("Failed to tar up toolchain")
		      
    return self.success()
