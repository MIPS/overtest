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
from Action import Action
from IMGAction import IMGAction
from Config import CONFIG

# MeOS Tests

class A117792(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117792
    self.name = "MeOS Tests"
    self.run_all_configs = False

  # Execute the action.
  def run(self):
    METAG_INST_ROOT = self.config.getVariable("METAG_INST_ROOT")
    meoslib_version = self.testrun.getVersion("MeOSLib")

    # What configurations should be run
    interrupt_models = self.config.getVariable("Interrupt Models")
    library_variants = self.config.getVariable("Library Variants")
    interrupt_stack = self.config.getVariable("Fast Interrupt Stack")
    force_meta = self.config.getVariable("Force META ISA")
    if " " in interrupt_models or " " in library_variants or " " in interrupt_stack:
      self.run_all_configs = True

    env={}
    env['PATH'] = os.environ['PATH']
    env['TEST_INT_MODELS'] = interrupt_models
    env['VARIANTS'] = library_variants
    env['FAST_STACKS'] = interrupt_stack
    env['TOOLKIT_VERSION'] = self.testrun.getVersion("MetaMtxToolkit")
    if env['TEST_INT_MODELS'] == "$(FAST_NAME)":
      env['LFLAGS_GEN'] = "-minterrupts=fastint"
    if force_meta:
      if 'LFLAGS_GEN' in env:
        env['LFLAGS_GEN'] += " -mno-minim"
      else:
        env['LFLAGS_GEN'] = "-mno-minim"

    if self.version == "Physical Board":
      # Run tests using a DA
      da = self.getResource("Debug Adapter")
      da_name = da.getAttributeValue("DA Name")

      host = self.getResource("Execution Host")
      cvsroot = host.getAttributeValue("KL metag CVSROOT")

      if meoslib_version in ("5.4.6", "5.4.7", "5.4.8", "5.4.9", "5.4.10", "5.4.11"):
        result = self.execute(command=["tar", "-xzf", os.path.join(CONFIG.shareddir,
                                                      "source_temp", "meos", "%s.tar.gz" % meoslib_version)])
        if result != 0:
          self.error("Unable to obtain source for meos %s" % meoslib_version)
        
        indent_path = self.neoSelect("Indent", "2.2.9")
        if indent_path is None:
          self.error("Unable to locate Indent 2.2.9")
        indent_path = os.path.join(indent_path, "bin")

        env['PATH'] = CONFIG.makeSearchPath([indent_path, env['PATH']])
        meos_dir = os.path.join(self.getWorkPath(), meoslib_version)
        test_command = ["make", "testclean", "test"]
      else:
        ccs_version=meoslib_version
        if ccs_version == "scratch":
          ccs_version=":MAX"
        if not self.ccsCheckout("metag/tools/libs/meos/ccs/meoslib.ccs", "MeOSLib",
                                ccs_version, cvsroot):
          self.error("Unable to check out MeOSLib:%s" % meoslib_version)
  
        if meoslib_version == "scratch":
          meos_src = os.path.join(self.getWorkPath(), "metag", "tools", "libs", "meos", "meoslib")
          if self.execute(workdir=meos_src, env={"CVSROOT":cvsroot}, command=[CONFIG.cvs, "update", "-dPA"]) != 0:
            self.error("Unable to update meos to head source")
  
        meos_dir=os.path.join(self.getWorkPath(), "metag", "tools", "libs", "meos")
        test_command = ["make", "-f", "build.mk", "test"]

      board_type = self.config.getVariable("Target Board")

      env['MEOS_BOARD'] = "generic_tcf"

      # Workaround test system bug
      if meoslib_version == "5.3.2.0":
        env['BOARD_FEATURES'] = "2 1 DSP atp mtp NOLITE NOGP"

      TARGET_CPU = "metag"
      CORE = "meta"
      if board_type == "Chorus 2 Metamorph":
        env['MEOS_BOARD'] = "atp120dp_ocm"
        # Workaround test system bug
        if meoslib_version == "5.3.2.0":
          env['BOARD_FEATURES'] = "4 2 1 DSP atp NOLITE NOGP"
      elif board_type == "MTX122 FPGA":
        env['TARGET_CPU'] = "mtxg"
        env['MEOS_BOARD'] = "mtx"
        CORE="mtx"
        # Workaround test system bug
        if meoslib_version == "5.3.2.0":
          env['BOARD_FEATURES'] = "1 atp MTX NOLITE NOGP"

      if board_type == "FRISA FPGA":
        env['BOARD_DSP_THREADS'] = "4"

      env['DA'] = da_name
      env['TEST_LOG'] = os.path.join(self.getWorkPath(), "meostests.log")
      env['METAG_INST_ROOT'] = METAG_INST_ROOT
      env['PREBUILT_MEOS'] = METAG_INST_ROOT
      env['PATH'] = CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo), env['PATH']])
      env['CODESCAPE_VER'] = "7.1.1.8:x32"
      env['CORE'] = CORE
      env['BOARD'] = env['MEOS_BOARD']

      if self.execute(command=test_command, env=env,workdir=meos_dir) != 0:
        self.error("Failed to run meos testsuite")

      # Now parse the log file
      if not os.path.exists(env['TEST_LOG']):
        self.error("Unable to find log file")

      self.parseLogFile(env['TEST_LOG'])
      self.registerLogFile(env['TEST_LOG'])

    return True

  def parseLogFile(self, log_file):
    """
    Parse the meos log file
    """
  
    try:
      fh = open(log_file)
    except OSError:
      self.error("Failed to open log file: %s" % log_file)
  
    timing_block = 0
    log_block = False
    passed = False
    parse_failure = False
    test_name = None
    results = {}
    for line in fh.read().splitlines():
      if timing_block != 0:
        if line == "---":
          self.testsuiteSubmit(test_name, passed, extendedresults=results)
          timing_block = 0
          continue
        if line.startswith("(THR 0)"):
          line = line[7:]
        if line == "Timing Test Test":
          timing_block = 2
          continue
        if timing_block == 2:
          info = line.split(":")
          if len(info) == 2:
            result_name = info[0].strip()
            info[1] = info[1].strip()
            if result_name in ("Interrupt stack @", "Interrupt mode"):
              continue
  
            result_value = None
            try:
              result_value = int(info[1])
            except ValueError:
              pass
            if result_value == None:
              try:
                result_value = float(info[1])
              except ValueError:
                pass
            if result_value == None:
              result_value = info[1]
  
            results[result_name] = result_value
            continue
          if line == "---------- ---------- ---------- ---------- --- --- -------------":
            timing_block = 3
          continue
        if timing_block == 3:
          if line == "Test done":
            timing_block = 4
          info = line.split(None, 6)
          if len(info) == 7:
            try:
              results[info[-1]] = float(info[0])
            except ValueError:
              pass
          continue
        continue
  
      if line.startswith("--- "):
        log_block = True
        continue
      if line == "---":
        log_block = False
        continue
      if log_block:
        continue
      if line.startswith("test="):
        # Found a valid test
        # test=kernel/ectx variant=rel ints=legacy intstack=no flavour=fullfat result=pass log=tests/atp120dp_ocm/meta/rel/kernel/ectx/ectx.log runtime=0:09.08
        fields=line.split()
        if len(fields) < 7:
          self.error("Badly formed result: %s" % line)

        fielddict = {}
        for field in fields:
          parts = field.split("=", 1)
          if len(parts) == 2:
            fielddict[parts[0]] = parts[1]

        if not "test" in fielddict:
          parse_failure = True
          continue
        
        test_name = fielddict["test"]
        if test_name == "regression/timing":
          timing_block = 1
          results = {}
  
        if self.run_all_configs and "variant" in fielddict and "ints" in fielddict and "intstack" in fielddict:
          test_name += "_%s_%s_%s" % (fielddict["variant"], fielddict["ints"], fielddict["intstack"])

        if "flavour" in fielddict:
          test_name += "_%s" % fielddict["flavour"]
  
        if "result" in fielddict:
          passed = (fielddict["result"] == "pass")
        else:
          passed = False
  
        if "runtime" in fielddict:
          runtime = fielddict["runtime"]
        else:
          runtime = "unknown"
  
        self.testsuiteSubmit(test_name, passed, extendedresults={"runtime":runtime})

    return parse_failure
