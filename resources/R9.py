from Resource import Resource
from OvertestExceptions import *
from Config import CONFIG
import os
import time
from utils.TerminalUtilities import *
import getopt

class R9(Resource):
  """
  A class to manage the Target Board resources
  """
  RESOURCETYPEID=9

  def __init__(self, data):
    """
    Initialise the class
    """
    Resource.__init__(self, data)

  def findMaxVersion(self, versions):
    """
    Find the largest numeric version in the list
    """
    max_version=0
    for version in versions:
      if version.isdigit():
        if int(version) > max_version:
          max_version = int(version)
    return max_version

  def initialise(self):
    """
    Run the initialisation commands
    """
    # Decide if this board needs initialising
    try:
      reprogram_host=self.getAttributeValue("Re-Program Host")
    except ResourceException:
      reprogram_host=None

    try:
      core_revision_family = self.getRequestedAttributeValues("Core Revision Family")
      if len(core_revision_family) != 1:
        self.error("Multiple core families requested")
      core_revision_family = core_revision_family[0]
    except ResourceException:
      core_revision_family = None

    if reprogram_host == None:
      # Now determine what core is supposed to be loaded
      try:
        core_revision=self.getAttributeValues("Core Revision")
        if len(core_revision) != 1:
          self.error("Multiple core revisions requested")
        core_revision = core_revision[0]

      except ResourceException:
        self.error("Board is missing core revision attribute")
    else:
      # Now determine what core is supposed to be loaded
      try:
        core_revision=self.getRequestedAttributeValues("Core Revision")
        if len(core_revision) != 1:
          self.error("Multiple core revisions requested")
        core_revision = core_revision[0]

      except ResourceException:
        core_revision = None

      # When there is no core, try to infer it using the '<core> VHDL Version' attribute
      if core_revision == None:
        foundvhdlversion = False 
        for attribute in self.requestedattributes.keys():
          if attribute.endswith(" VHDL Version"):
            if foundvhdlversion:
              self.error("Multiple VHDL Versions requested")
            core_revision = attribute[:-13]
            foundvhdlversion = True
        
      if core_revision == None and core_revision_family == None:
        # No core... no programming!
        if 'Core Revision' in self.attributes:
          del self.attributes['Core Revision']
        if 'Core Revision Family' in self.attributes:
          del self.attributes['Core Revision Family']
        if 'Reset State' in self.attributes:
          del self.attributes['Reset State']
        for attr in self.attributes.keys():
          if attr.endswith(" VHDL Version"):
            del self.attributes[attr]
        return True

      # if only one of the core revision or family is set, then infer the other
      if core_revision == None:
        if (core_revision_family+"DBG") in self.getAttributeValues("Core Revision"):
          core_revision = core_revision_family+"DBG"
        elif core_revision_family in self.getAttributeValues("Core Revision"):
          core_revision = core_revision_family
        else:
          self.error("Unable to find any variant of core revision family %s"%core_revision_family)

      if core_revision_family == None:
        # The core revision family may still be required if the core revision is
        # an MTP core (though HTPs do not have a family as there is only one variant)
        search_family = core_revision
        # Strip the dbg prefix for debug variants of the cores
        if search_family.endswith("DBG"):
          search_family = search_family[:-3]

        # See if the core family is in the supported core families
        try:
          core_families = self.getAttributeValues("Core Revision Family")
          if search_family in core_families:
            core_revision_family = search_family
        except ResourceException, e:
          pass

      if core_revision_family != None and not core_revision.startswith(core_revision_family):
        self.error("Mismatch of core revision family and core revision")

      # Force the Core Revision and Core Revision Family attributes to the single values
      self.attributes['Core Revision'] = [core_revision]
      if core_revision_family == None:
        if 'Core Revision Family' in self.attributes:
          del self.attributes['Core Revision Family']
      else:
        self.attributes['Core Revision Family'] = [core_revision_family]

      # Now strip all the attributes ending ' VHDL Version' that do not match the core
      for attribute in self.attributes.keys():
        if attribute.endswith(" VHDL Version") and attribute != "%s VHDL Version" % core_revision:
          del self.attributes[attribute]

      core_directory=core_revision.lower()

      try:
        fpga_type=self.getAttributeValues("FPGA Type")
        if len(fpga_type) != 1:
          self.error("Multiple FPGA types requested")
        fpga_type = fpga_type[0]
      except ResourceException:
        self.error("Missing FGPA Type attribute")

      try:
        # Check that the user asked for the correct "<core> VHDL Version"
        for attribute in self.requestedattributes.keys():
          if attribute.endswith(" VHDL Version") and attribute != "%s VHDL Version" % core_revision:
            self.error("Attribute %s not valid for core %s" % (attribute, core_revision))

        version = self.getRequestedAttributeValues("%s VHDL Version" % (core_revision))
        if len(version) != 1:
          self.error("Multiple VHDL versions requested")
        version = version[0]
      except ResourceException:
        max_version = self.findMaxVersion(self.getAttributeValues("%s VHDL Version" % (core_revision)))
        if max_version == 0:
          self.error("No valid %s VHDL Version found" % (core_revision))
        version = str(max_version)

      self.attributes["%s VHDL Version" % (core_revision)] = [version]

      # Set the bitstream(s) for the daughterboard
      core_path = os.path.join(CONFIG.bitstreams, core_directory, version)
      daughterboard_type = self.getAttributeValue("TCF Daughterboard").lower()
      fpga_file = daughterboard_type
      if " " in fpga_file:
        fpga_file = fpga_file.split(" ").pop()

      try:
        debug_type = self.getAttributeValue("Debug Type")
      except ResourceException:
        self.error("Missing Debug Type attribute")

      fpga_dir = fpga_file
      if debug_type == "CJTAG":
        fpga_file = "%s_cjtag" % fpga_file

      # Reset the second FPGA if it is not used
      daughterboardb = os.path.join(CONFIG.bitstreams, fpga_dir, "dummy.bit")

      # Search for the bitstreams (error checking)
      if not os.path.exists(os.path.join(core_path, "%s.bit" % (fpga_file))) and \
         not os.path.exists(os.path.join(core_path, "%sa.bit" % (fpga_file))):
        self.error("Could not find any bitstream (single or dual): %s"% core_path)

      if (os.path.exists(os.path.join(core_path, "%sa.bit" % (fpga_file))) and \
          not os.path.exists(os.path.join(core_path, "%sb.bit" % (fpga_file)))) or \
         (os.path.exists(os.path.join(core_path, "%sb.bit" % (fpga_file))) and \
          not os.path.exists(os.path.join(core_path, "%sa.bit" % (fpga_file)))):
        self.error("Found one bitstream of a pair: %s"% core_path)

      if os.path.exists(os.path.join(core_path, "%s.bit" % (fpga_file))) and \
         os.path.exists(os.path.join(core_path, "%sa.bit" % (fpga_file))):
        self.error("Found a pair of bitstreams and a single: %s"% core_path)

      # Set the bitstreams
      if os.path.exists(os.path.join(core_path, "%s.bit" % (fpga_file))):
        daughterboarda=os.path.join(core_path, "%s.bit" % (fpga_file))
      elif os.path.exists(os.path.join(core_path, "%sa.bit" % (fpga_file))):
        if not "dual" in daughterboard_type:
          self.error("Unable to load pair of bitstreams to single FPGA")
        daughterboarda = os.path.join(core_path, "%sa.bit" % (fpga_file))
        daughterboardb = os.path.join(core_path, "%sb.bit" % (fpga_file))

      # Set the default bitstream for the mainboard
      mainboard_type = self.getAttributeValue("TCF Mainboard").lower()

      mainboard_dir = mainboard_type
      if debug_type == "CJTAG":
        mainboard_type = "%s_cjtag" % mainboard_type
      mainboard_version = "default"
      mainboard = os.path.join(CONFIG.bitstreams, mainboard_dir, mainboard_version, "%s.bit" % mainboard_type)

      # Override the default mainboard based on the core
      if os.path.exists(os.path.join(CONFIG.bitstreams, core_directory, "%s.bit" % mainboard_type)):
        mainboard = os.path.join(CONFIG.bitstreams, core_directory, "%s.bit" % mainboard_type)

      # Override the mainboard if the user requested it
      try:
        mainboard_version = self.getRequestedAttributeValue("TCF Mainboard Version")
        mainboard = os.path.join(CONFIG.bitstreams, mainboard_dir, mainboard_version, "%s.bit"%mainboard_type)
      except ResourceException:
        # Nothing requested, do nothing
        pass

      self.attributes["TCF Mainboard Version"] = [mainboard_version]

      current_dir = os.path.dirname( os.path.realpath( __file__ ) )
      programmer = os.path.join(current_dir, "..", "addons", "fpga_programmer")
      programmer = os.path.realpath(programmer)

      command=[CONFIG.neo, 'run_dascript', 
               os.path.join(programmer, 'program_fpga2.py'),
               "-h", reprogram_host]

      # Do not program the lx110 until the hardware can cope with a soft-reset
      if mainboard_dir != "lx110":
        command.extend(["-m", mainboard])

      command.extend(["-a", daughterboarda])

      if "dual" in daughterboard_type:
        command.extend(["-b", daughterboardb])

      if mainboard_dir == "lx110":
        command.extend(["--dut-clock", "30"])

      try:
        result = self.execute(timeout=300,
                              command=command)
      except TimeoutException, e:
        return self.transientError("Timeout when programming FPGA")

      if result != 0:
        return self.transientError("Failed to program FPGA, check logs")

      time.sleep(2)

    boardtype = self.getAttributeValue("Board Type")

    # FPGAs need extra initialisation
    if boardtype == "FPGA":
      if core_revision == None:
        # No core no config
        return True

      # Some cores do not require initialisation
      if core_revision in ["MTX", "META122"]:
        None
      else:
        # Assume for now that all other cores are META 2
        try:
          DA = self.getResource("Debug Adapter")
        except:
          self.error("Failed to find Debug Adapter")
    
        try:
          da_name = DA.getAttributeValue("DA Name")
        except ResourceException:
          self.error("Debug Adapter has no DA Name attribute")
    
        command = [CONFIG.neo, 'run_dascript', 'fpga_init.py', "-D", da_name]
    
        try:
          reset_state=self.getRequestedAttributeValues("Reset State")
          if len(reset_state) != 1:
            self.error("Multiple reset states requested")

          self.attributes['Reset State'] = resetstate[:]
          reset_state = reset_state[0]
          if reset_state in ["CLOCK_GATING_ON", "CLOCK_GATING_OFF"]:
            None
          else:
            self.error("Unknown clock gating value: %s"%reset_state)

          # Determine which cores are MTP or HTP
          HTP_CORES=["213_2t1d", "213_2t2d", "214_4t2df", "COMET", "META2", "META213"]
          MTP_CORES=["HERON", "HERONDBG", "KINGFISHER", "KINGFISHERDBG", "STORK", "STORK64", "STORK64DBG", "STORKDBG"]
          if core_revision in HTP_CORES:
            reset_state="HTP_%s"%reset_state
          elif core_revision in MTP_CORES:
            reset_state="MTP_%s"%reset_state
          else:
            self.error("Unable to determine if core '%s' is MTP or HTP"%core_revision)

          command.append("-s")
          command.append(reset_state)

        except ResourceException:
          # If the user did not request an explicit clock gating setting then do nothing
          if 'Reset State' in self.attributes:
            del self.attributes['Reset State']
    
        try:
          result = self.execute(timeout=100,command=command)
        except TimeoutException, e:
          return self.transientError("Timeout when initialising FPGA")
    
        if result != 0:
          return self.transientError("Failed to initialise FPGA, check logs")

    return True

  def interactiveUsage(self):
    """
    Help for running an interactive update of a target board
    """
    print "Submit a new version of various FPGA bitstreams"
    print "==============================================="
    print "1) Add a new core with a single bitstream"
    print "   --core=<corename> --version=<version>"
    print "   [--cjtag]"
    print "   [--lx330=<bitstream>]"
    print "   [--lx760=<bitstream>]"
    print "2) Add a new core with dual bitstreams"
    print "   --core=<corename> --version=<version>"
    print "   [--cjtag]"
    print "   [--lx330a=<bitstream> --lx330b=<bitstream>]"
    print "   [--lx760a=<bitstream> --lx760b=<bitstream>]"
    print "3) Add a special mainboard bitstream for a core."
    print "   --core=<corename>"
    print "   [--cjtag]"
    print "   [--lx80=<bitstream>]"
    print "   [--lx160=<bitstream>]"
    print "   [--lx110=<bitstream>]"
    print "4) Add a new mainboard version for all cores"
    print "   --version=<mainboardversion>"
    print "   [--cjtag]"
    print "   [--lx80=<bitstream>]"
    print "   [--lx160=<bitstream>]"
    print "   [--lx110=<bitstream>]"

  def interactiveUpdate(self, args):
    """
    Provide a simple interface to update (some aspects of) the Target Board type of resource
    """
    import shutil
    try:
      opts, args = getopt.getopt(args, "", ["cjtag", "core=", "version=", "lx330=", "lx760=", "lx330a=", "lx330b=", "lx760a=", "lx760b=", "lx80=", "lx160=", "lx110="])
    except getopt.GetoptError, e:
      self.interactiveUsage()
      return 1
    
    if len(opts) == 0:
      self.interactiveUsage()
      return 1

    cjtag = False
    core = None
    version = None
    lx330 = None
    lx760 = None
    lx330a = None
    lx330b = None
    lx760a = None
    lx760b = None
    lx80 = None
    lx160 = None
    lx110 = None

    for o, a in opts:
      if o == "--cjtag":
        cjtag = True
      if o == "--core":
        core = a
      elif o == "--version":
        version = a
      elif o == "--lx330":
        lx330 = a
      elif o == "--lx330a":
        lx330a = a
      elif o == "--lx330b":
        lx330b = a
      elif o == "--lx760":
        lx760 = a
      elif o == "--lx760a":
        lx760a = a
      elif o == "--lx760b":
        lx760b = a
      elif o == "--lx80":
        lx80 = a
      elif o == "--lx160":
        lx160 = a
      elif o == "--lx110":
        lx110 = a

    # Check for valid usage
    # 1) A version is mandatory for mainboards
    if core == None and version == None:
      print "ERROR: Please specify a version"
      self.interactiveUsage()
      return 1

    # 2) A core requires either a single OR dual bitstreams
    if core != None:
      if lx330 != None and lx330a != None:
        print "ERROR: Please specify either an lx330 OR lx330a and lx330b bitstream"
        self.interactiveUsage()
        return 1
      if lx760 != None and lx760a != None:
        print "ERROR: Please specify either an lx760 OR lx760a and lx760b bitstream"
        self.interactiveUsage()
        return 1
      if lx330 == None and lx330a == None and lx80 == None and lx160 == None \
         and lx760 == None and lx760a == None and lx110 == None:
        print "ERROR: Please specify at least one bitstream"
        self.interactiveUsage()
        return 1
      if version == None and (lx330 != None or lx330a != None \
                              or lx760 != None or lx760a != None):
        print "ERROR: Please specify a version with a daughterboard bitstream"
        self.interactiveUsage()
        return 1

    # 3) A dual bitstream must have both specified
    if (lx330a != None and lx330b == None) or \
       (lx330b != None and lx330a == None):
      print "ERROR: Please specify both lx330a and lx330b bitstreams"
      self.interactiveUsage()
      return 1

    if (lx760a != None and lx760b == None) or \
       (lx760b != None and lx760a == None):
      print "ERROR: Please specify both lx760a and lx760b bitstreams"
      self.interactiveUsage()
      return 1

    # 4) A mainboard update can't have any daughterboard bitstreams
    if core == None and (lx330 != None or lx330a != None or lx330b != None \
                         or lx760 != None or lx760a != None or lx760b != None):
      print "ERROR: A mainboard update cannot include daughterboard bitstreams"
      self.interactiveUsage()
      return 1

    # 5) A mainboard update must have at least one of lx80 or lx160 or lx110 bitstreams
    if core == None and lx80 == None and lx160 == None and lx110 == None:
      print "ERROR: A mainboard update requires at least one lx80 or lx160 or lx110 bitstream"
      self.interactiveUsage()
      return 1

    # 6) Check the bitstreams exist
    for bitstream in [lx330, lx330a, lx330b, lx760, lx760a, lx760b, lx80, lx160, lx110]:
      if bitstream != None and not os.path.exists(bitstream):
        print "ERROR: Bitstream file not found: %s" % bitstream
        return 1

    cjtag_str = ""
    if cjtag:
      cjtag_str = "(CJTAG) "

    # 7) Submit the new bitstreams
    if core == None:
      # 7a) Submit a new mainboard
      if lx80 != None:
        if not self.submitMainboard(cjtag, "lx80", version, lx80):
          return 1
        print "Version %s of Lx80 %sready to use" % (version, cjtag_str)
      if lx160 != None:
        if not self.submitMainboard(cjtag, "lx160", version, lx160):
          return 1
        print "Version %s of Lx160 %sready to use" % (version, cjtag_str)
      if lx110 != None:
        if not self.submitMainboard(cjtag, "lx110", version, lx110):
          return 1
        print "Version %s of Lx110 %sready to use" % (version, cjtag_str)
    else:
      # 7b) Submit a new core
      if lx330 != None:
        if not self.submitDaughterboard(cjtag, "lx330", core, version, [lx330]):
          return 1
        print "Version %s of %s %sready to use" % (version, core, cjtag_str)
      elif lx330a != None:
        if not self.submitDaughterboard(cjtag, "lx330", core, version, [lx330a, lx330b]):
          return 1
        print "Version %s of %s %sready to use" % (version, core, cjtag_str)

      if lx760 != None:
        if not self.submitDaughterboard(cjtag, "lx760", core, version, [lx760]):
          return 1
        print "Version %s of %s %sready to use" % (version, core, cjtag_str)
      elif lx760a != None:
        if not self.submitDaughterboard(cjtag, "lx760", core, version, [lx760a, lx760b]):
          return 1
        print "Version %s of %s %sready to use" % (version, core, cjtag_str)

      if lx80 != None:
        if not self.submitSpecialMainboard(cjtag, "lx80", core, lx80):
          return 1
        print "Added special Lx80 %sbitstream for %s" % (cjtag_str, core)
      if lx160 != None:
        if not self.submitSpecialMainboard(cjtag, "lx160", core, lx160):
          return 1
        print "Added special Lx160 %sbitstream for %s" % (cjtag_str, core)
      if lx110 != None:
        if not self.submitSpecialMainboard(cjtag, "lx110", core, lx110):
          return 1
        print "Added special Lx110 %sbitstream for %s" % (cjtag_str, core)
      # Success

    if os.system("find %s -type d -and -not -perm -020 -exec chmod g+w {} \;" % (CONFIG.bitstreams)) != 0:
      print "ERROR: Unable to grant write access to: %s" % (CONFIG.bitstreams)
      return 1

    return 0

  def submitMainboard(self, cjtag, fpga, version, bitfile):
    """
    Submit a custom mainboard bitstream

    :param fpga: The type of FPGA
    :type fpga: string
    :param version: The new version
    :type version: string
    :param bitfile: The bitstream
    :type bitfile: path
    :return: success
    :rtype: boolean
    """
    import shutil
    if os.system("mkdir -p %s/%s/%s" % (CONFIG.bitstreams, fpga, version)) != 0:
      print "ERROR: Unable to create bistream directory: %s/%s/%s" % (CONFIG.bitstreams, fpga, version)
      return False

    cjtag_suf = ""
    if cjtag:
      cjtag_suf = "_cjtag"

    try:
      shutil.copy(bitfile, "%s/%s/%s/%s%s.bit" % (CONFIG.bitstreams, fpga, version, fpga, cjtag_suf))
    except Exception, e:
      print "ERROR: Unable to copy bitstream %s"% e.message
      return False

    # Find the TCF Mainboard Version attribute
    values = {}
    values['resourcetypeid'] = R9.RESOURCETYPEID
    values['name'] = "TCF Mainboard Version"
    values['islookup'] = True
    verattributeid = self.ovtDB.addAttribute(values)

    # Add the core (if it doesn't exist)
    versionid = self.ovtDB.addAttributeValue(verattributeid, version, False)

    # Link the version to all the TCF boards
    resources = self.ovtDB.getResources({})

    # Filter based on Target Board, then FPGA Type and then Mainboard == '<fpga>'
    targetresources = []
    for resourceid in resources[0]:
      types = resources[0][resourceid]['related']
      addit = True
      for typeid in types[0]:
        if types[0][typeid]['data'] != "Target Board":
          addit = False
          continue
        attributes = types[0][typeid]['related']
        foundmainboard = False
        for attributeid in attributes[0]:
          if attributes[0][attributeid]['data'] == 'TCF Mainboard':
            values = attributes[0][attributeid]['related']
            for valueid in values[0]:
              if values[0][valueid]['data'].lower() == fpga.lower():
                foundmainboard = True
          if attributes[0][attributeid]['data'] == 'Debug Type':
            values = attributes[0][attributeid]['related']
            for valueid in values[0]:
              if cjtag == (values[0][valueid]['data'].lower() != 'cjtag'):
                addit = False
        if not foundmainboard:
          addit = False
      if addit:
        targetresources.append(resources[0][resourceid])

    # Link the new version to all TCF boards with the correct mainboard
    for resource in targetresources:
      self.ovtDB.specifyAttribute(resource['id'], verattributeid, versionid)

    return True

  def submitDaughterboard(self, cjtag, fpga, core, version, bitfiles):
    """
    Submit a single bitstream for a daughterboard

    :param fpga: The type of FPGA
    :type fpga: string
    :param core: The new core
    :type core: string
    :param version: The new version
    :type version: string
    :param bitfiles: The bitstreams
    :type bitfiles: array of path
    :return: success
    :rtype: boolean
    """
    import shutil
    if os.system("mkdir -p %s/%s/%s" % (CONFIG.bitstreams, core.lower(), version)) != 0:
      print "ERROR: Unable to create bistream directory: %s/%s/%s" % (CONFIG.bitstreams, core.lower(), version)
      return False

    try:
      cjtag_suf = ""
      if cjtag:
        cjtag_suf = "_cjtag"

      single_bitfile = "%s/%s/%s/%s%s.bit" % (CONFIG.bitstreams, core.lower(), version, fpga.lower(), cjtag_suf)
      duala_bitfile = "%s/%s/%s/%s%sa.bit" % (CONFIG.bitstreams, core.lower(), version, fpga.lower(), cjtag_suf)
      dualb_bitfile = "%s/%s/%s/%s%sb.bit" % (CONFIG.bitstreams, core.lower(), version, fpga.lower(), cjtag_suf)
      if len(bitfiles) == 1:
        if os.path.exists(duala_bitfile):
          print "ERROR: Dual bitstreams found but single bitstream submitted: %s" % duala_bitfile
          return False
        if os.path.exists(dualb_bitfile):
          print "ERROR: Dual bitstreams found but single bitstream submitted: %s" % dualb_bitfile
          return False
        shutil.copy(bitfiles[0], single_bitfile)
      elif len(bitfiles) == 2:
        if os.path.exists(single_bitfile):
          print "ERROR: Single bitstream found but dual bitstreams submitted: %s" % single_bitfile
          return False
        shutil.copy(bitfiles[0], duala_bitfile)
        shutil.copy(bitfiles[1], dualb_bitfile)
      else:
        print "ERROR: Unexpected number of bistreams: %s" % bitfiles
        return False
    except Exception, e:
      print "ERROR: Unable to copy bitstream %s"% e.message
      return False

    # Find the Core Revision attribute
    values = {}
    values['resourcetypeid'] = R9.RESOURCETYPEID
    values['name'] = "Core Revision"
    values['islookup'] = True
    revattributeid = self.ovtDB.addAttribute(values)

    # Add the core (if it doesn't exist)
    corerevisionid = self.ovtDB.addAttributeValue(revattributeid, core.upper(), False)

    # Add the VHDL version attribute (if it doesn't exist)
    values = {}
    values['resourcetypeid'] = R9.RESOURCETYPEID
    values['name'] = "%s VHDL Version" % core.upper()
    values['islookup'] = True
    coreattributeid = self.ovtDB.addAttribute(values)

    # Add the version (if it doesn't exist)
    coreversionid = self.ovtDB.addAttributeValue(coreattributeid, version, False)

    # Link the version to all the TCF boards
    resources = self.ovtDB.getResources({})

    # Filter based on Target Board, then FPGA Type and then '<fpga> in TCF Daughterboard'
    targetresources = []
    for resourceid in resources[0]:
      types = resources[0][resourceid]['related']
      addit = True
      for typeid in types[0]:
        if types[0][typeid]['data'] != "Target Board":
          addit = False
          continue
        attributes = types[0][typeid]['related']
        founddaughterboard = False
        for attributeid in attributes[0]:
          if attributes[0][attributeid]['data'] == 'TCF Daughterboard':
            values = attributes[0][attributeid]['related']
            for valueid in values[0]:
              # Check for single or dual board requirements
              if len(bitfiles) == 2 and ("dual %s" % fpga.lower()) in values[0][valueid]['data'].lower():
                founddaughterboard = True
              if len(bitfiles) == 1 and fpga.lower() in values[0][valueid]['data'].lower():
                founddaughterboard = True
          if attributes[0][attributeid]['data'] == 'Debug Type':
            values = attributes[0][attributeid]['related']
            for valueid in values[0]:
              if cjtag == (values[0][valueid]['data'].lower() != 'cjtag'):
                addit = False
        if not founddaughterboard:
          addit = False
      if addit:
        targetresources.append(resources[0][resourceid])

    # Link the new version to all relevant TCF boards
    for resource in targetresources:
      self.ovtDB.specifyAttribute(resource['id'], coreattributeid, coreversionid)
      self.ovtDB.specifyAttribute(resource['id'], revattributeid, corerevisionid)

    return True 

  def submitSpecialMainboard(self, cjtag, fpga, core, bitfile):
    """
    Submit a special mainboard for a particular core

    :param fpga: The type of FPGA
    :type fpga: string
    :param core: The new core
    :type core: string
    :param version: The new version
    :type version: string
    :param bitfiles: The bitstreams
    :type bitfiles: array of path
    :return: success
    :rtype: boolean
    """
    import shutil
    if os.system("mkdir -p %s/%s" % (CONFIG.bitstreams, core.lower())) != 0:
      print "ERROR: Unable to create bistream directory: %s/%s" % (CONFIG.bitstreams, core.lower())
      return False

    cjtag_suf = ""
    if cjtag:
      cjtag_suf = "_cjtag"

    try:
      shutil.copy(bitfile, "%s/%s/%s%s.bit" % (CONFIG.bitstreams, core.lower(), fpga.lower(), cjtag_suf))
    except Exception, e:
      print "ERROR: Unable to copy bitstream %s"% e.message
      return False

    return True
