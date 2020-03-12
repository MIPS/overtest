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
# onetest.py
#
# This script will load an LDLK generated script, run the target, and pipe
# logging to the console.  Once the target has stopped, this script will run
# the next script.
#
import os
import textwrap
import time
import getopt
import sys
import traceback
from CSUtils import DA

def Usage():
  """
  Print all options and environment overrides
  """
  print "OneTest version 2.0"
  print "Usage:"
  print "OneTest <options> <load script> [arg1] [arg2]..."
  print "-D <DA identifier --DA=<DA identifier>"
  print "        Specify the debug adaptor to connect to"
  print "-F <path>         --fileserver=<path>"
  print "        Specify the jailed fileserver root"
  print "-P <script>       --postreset <script>"
  print "        Add a script to execute after reset. Multiple scripts are permitted"
  print "-T <seconds>      --timeout <seconds>"
  print "        Specify the target timeout in seconds"
  print "{no short option} --suppress-dialog"
  print "        Hide the load progress dialog"
  print "{no short option} --no-suppress-dialog"
  print "        Show the load progress dialog"
  print ""
  print "Default options can be adjusted using environment variables."
  print "A command line option will however override any environment setting where"
  print "applicable"
  print ""
  print "METAT_USE_TARGET          - Specify the default debug adapter ID"
  print "METAT_ONETEST_TIMEOUT     - Adjust the default timeout (300 seconds)"
  print "METAT_ONETEST_SUPPRESSDLG - Prevents the progress dialog when loading apps"

def FormatExceptionInfo():
  """
  For custom exception handling, this function will return the current stack trace
  as a string.
  """
  error_type, error_value, trbk = sys.exc_info()
  tb_list = traceback.format_tb(trbk)
  s = "Error: %s \nDescription: %s \nTraceback:" % (error_type.__name__, error_value)
  for i in tb_list:
    s += "\n" + i
  return s

def NumThreads() :
  """
  Find the number of threads
  """
  num_threads = 0
  for target in DA.IterateTargets(True):
    if DA.SelectTarget (target):
      num_threads += 1
    
  return num_threads

def RunPostResetScripts(scripts) :
  """
  Run a series of scripts
  """
  if len(scripts) > 0:
    print("Running post reset scripts:")
    for script in scripts:
      if os.path.exists(script):
        print script
        file = open(script)
        script = file.read()
        file.close()
        exec( script )
  
def LoadProgramFiles(path) :
  """
  Load the script
  """
  load_success = True
  try:
    DA.LoadProgramFileEx(path, ShowProgress=suppress_dialog)
  except Exception, e:
    load_success = False

  dir, file = os.path.split(path)
  olddir = os.getcwd()
  os.chdir(dir)
  try:
    try:
      modulename = os.path.splitext(file)[0]
      m = __import__(modulename)
      elf_files = m.elf_files
    except Exception, e:
      load_success = False
  finally :
    os.chdir(olddir)

  n = 0
  for target in DA.IterateTargets():
    if elf_files["e%d" % n] != 0:
      threads_loaded[target] = True
    else:
      threads_loaded[target] = False
    n += 1
  return load_success

def GetMilliTime() :
  """
  Current time in milliseconds
  """
  return int(time.time()*1000)

def RunAllLoadedThreads():
  """
  Run all the threads that have been loaded
  """
  for target in DA.IterateTargets():
    if threads_loaded[target]:
      if DA.SelectTarget(target):
        print "Running %s" % DA.GetTargetInfo(target)
        DA.Run()
        threads_started[target] = True
      else:
        print "Failed to SelectTarget()"

def StopAllLoadedThreadsRunning() :
  """
  Stop all threads
  """
  thread_running = False
  for target in DA.IterateTargets():
    if threads_loaded[target]:
      if DA.SelectTarget (target):
        if is_running and threads_started[target]:
          print "Stopped thread on: %s" % DA.GetTargetInfo(target)
          DA.Stop()
          threads_started[target] = False
          threads_stopped[target] = True
          thread_running = True
      else:
        print "Failed to SelectTarget()"

  return thread_running

def ArgsForAllLoadedThreads(args) :
  """
  Inject arguments in to all loaded threads with _metag_argv
  """
  if len(args) == 0:
    return
  for target in DA.IterateTargets():
    if threads_loaded[target]:
      if DA.SelectTarget (target):
        print "Args for thread %s" % DA.GetTargetInfo(target)
        addr = DA.EvaluateSymbol ("_metag_argv")
        i = 0
        for arg in args:
          arga = DA.ReadLong( addr + (i*4) )
          print "Argument %d <%s> to %x" % (i, arg, arga)
          DA.WriteString( arga, arg )
          i += 1
        else:
          print("Failed to SelectTarget()")

def AnyLoadedThreadRunning() :
  thread_running = False
  for target in DA.IterateTargets():
    if threads_loaded[target]:
      if DA.SelectTarget (target):
        is_running = DA.IsRunning()
        thread_running |= is_running
        if not is_running and threads_started[target] :
            print "Thread stopped on: %s" % DA.GetTargetInfo(target)
            threads_started[target] = 0
            threads_stopped[target] = 0
  return thread_running

def OutputChannelData(s):
  """
  Read channel data
  """
  if (DA.ChannelDataReady(logf_channel)):
    while(DA.ChannelDataReady(logf_channel)):
      ch = DA.ChannelRead(logf_channel)
      if (s != "" and (ch == 0 or ch == 10)):
        Write(s)
        s = ""
      elif (ch != 13):
        s += chr(ch)
  return s

# For each thread that was run in a test, check the exit value
# Returns 0 if all executed threads passed.
# Returns 1 if any executed thread fails.

def ReportTestResult() :
  result = 0
  i = 0
  for target in DA.IterateTargets():
    if threads_loaded[target]:
      if DA.SelectTarget (target):
        txenable = DA.ReadRegister("TXENABLE")
        status   = DA.ReadRegister("TXSTATUS")
        pc       = DA.ReadRegister("PC")
        hreason  = (status >> 18) & 3
        is_mtx   = (txenable & (1<<11)) != 0

        if is_mtx:
          if (pc & 0xFFF80000) == 0x80900000:
            # Map MTX address
            pc = (pc & 0xFFE00000) | ((pc & 0x1FFFFF) >> 1)
          else :
            print "PC %x out of expected range for MTX" % pc

        # WORK NEEDED: This does not support MiniM exit paths

        if hreason == 0:
          # Expect SWITCH 0xC30006 trap to exit
          is_exit_switch = False
          if  is_mtx  :
            inst = DA.ReadWord(pc-2)
            is_exit_switch = ( inst == 0x9FF3 )
          else :
            inst = DA.ReadLong(pc)
            if inst != 0xAFC30006:
              inst = DA.ReadLong(pc-4)
            is_exit_switch = ( inst == 0xAFC30006 )

          if is_exit_switch:
            # D0Re0 is on the stack, fetch it
            stack_pointer = DA.ReadRegister("A0StP")
            exit_value = DA.ReadLong(stack_pointer - 4)
            if exit_value != 0:
              result = exit_value
              print "Thread %d FAILED: D0Re0: %d (%x)" %(i, exit_value, exit_value)
          elif threads_stopped[target]:
            print "Thread %d STOPPED AT: %x [PC=%x]" % (i, inst, pc)
          else :
            result = 1
            print "Thread %d FAILED: Unexpected SWITCH: %x [PC=%x]" % (i, inst, pc)
        else:# Halted for some other reason
          reason = "<UNKNOWN>"
          if hreason == 1:
            reason = "Unknown instruction"
          elif hreason == 2:
            reason = "Privilege violation"
          elif hreason == 3:
            reason = "Memory fault"
          print "Thread %d FAILED: %s [PC=%x]" % (i, reason, pc)
          result = 1
      # Keep track of thread number
      i += 1
    return result

def WriteMessage(msg) :
    print msg

def Write(msg) :
  if msg == "Failed to LoadProgramFile()":
    success = False
  print msg

# Configuration area

# Set the maxmimum time a test is permitted to take (in milliSeconds) before
# a time out is generated. (default 5 minutes)

test_max_time = 5 * 60 * 1000
da_name = None
fileserver_root = None
post_reset_scripts = []
suppress_dialog = False
logf_channel = 1

# If the environment variable METAT_ONETEST_TIMEOUT exists (and contains a
# sensible value) set our timeout to that number of seconds

if 'METAT_ONETEST_TIMEOUT' in os.environ:
  try:
    env_timeout = int(os.environ['METAT_ONETEST_TIMEOUT'])
    if env_timeout >= 0:
      test_max_time = env_timeout * 1000
  except ValueError:
    None # Ignore bad env values

if 'METAT_USE_TARGET' in os.environ:
  da_name = os.environ['METAT_USE_TARGET']

if 'METAT_ONETEST_SUPPRESSDLG' in os.environ:
  suppress_dialog = (os.environ['METAT_ONETEST_SUPPRESSDLG'] != "0")

try:
  opts, args = getopt.getopt(sys.argv[1:], "hD:F:P:T:", ["help", "DA=", 
                                                         "fileserver=", "postreset=", "timeout=",
                                                         "suppress-dialog", "no-suppress-dialog"])
except getopt.GetoptError:
  Usage()
  sys.exit(2)

for (o,a) in opts:
  if o in ("-D", "--DA"):
    da_name = a
  elif o in ("-F", "--fileserver"):
    fileserver_root = a
  elif o in ("-P", "--postreset"):
    post_reset_scripts.append(a)
  elif o in ("-T", "--timeout"):
    try:
      test_max_time = int(a) * 1000
    except ValueError:
      print "ERROR: Timeout value must be numeric"
      sys.exit(1)
  elif o in ("-h", "--help"):
    Usage()
    sys.exit(1)
  elif o == "--suppress-dialog":
    suppress_dialog = True
  elif o == "--no-suppress-dialog":
    suppress_dialog = False

if len(args) != 1:
  print "ERROR: Please specify a script to run"
  sys.exit(3)

test_file = os.path.abspath(args[0])
if fileserver_root == None:
  fileserver_root = os.path.dirname(test_file)

test_name = os.path.basename(test_file)

if da_name == None:
  print "Error: No debug adapter specified"
  sys.exit(4)

#######################################/

threads_loaded = {}
threads_started = {}
threads_stopped = {}
threads_strs = {}

DA.UseTarget(da_name)

for target in DA.IterateTargets():
  threads_loaded[target]       = False
  threads_started[target]      = False
  threads_stopped[target]      = False
  threads_strs[target]         = None

success = True
result = 1
begin = 0

print "=" * 80
print "OneTest. running: %s" % test_name

print textwrap.fill(" ".join(args[1:]), 80)
print "=" * 80
print ""

try:
  overall_time_taken = 0
  num_threads = NumThreads()
  DA.SetFileServerPath(fileserver_root)

  print "RUNNING TEST %s" % test_name
  print ""
  print "=" * 80
  print ""

  DA.HardReset()
  RunPostResetScripts( post_reset_scripts )

  # Attempt to load the program files
  if os.path.exists(test_file):
    success = LoadProgramFiles(test_file)
  elif os.path.exists(test_file + ".js"):
    success = LoadProgramFiles(test_file + ".js")
  elif os.path.exists(test_file + ".py"):
    success = LoadProgramFiles(test_file + ".py")
  else:
    success = False
    print "Can't find %s" % test_name

  if not success:
    print ("TEST FAILED TO LOAD = %s" % test_name).center("-")
  else:# load succeeded, run the tests, collect LogF data, and wait for the test fo finish
    test_timedout = 0
    next_slice = 0.5
    s = ""

    DA.SelectTarget(DA.GetFirstTarget())
    DA.WriteLong(0x87FFFFFC, 0xdebdab23)

    if DA.ChannelReserve(logf_channel):
      if DA.ChannelValidate(logf_channel):
        # Instantiate any arguments
        ArgsForAllLoadedThreads(args[1:])
    
        # Start the test
        begin = GetMilliTime()
        RunAllLoadedThreads()
        while AnyLoadedThreadRunning() and not test_timedout :
          s = OutputChannelData(s)
          # Time-out
          time.sleep(next_slice)
          if (GetMilliTime() - begin) > test_max_time :
            test_timedout = 1

        s = OutputChannelData(s)
    else:
      print "ERROR: Failed to reserve logf channel"
      sys.exit(4)
    
    time_taken = GetMilliTime() - begin
    overall_time_taken += time_taken

    print ""
    print "=" * 80
    print ""

    if test_timedout:
      print "TEST TIMED OUT after %d seconds: %s" % (int(time_taken / 1000), test_name)
    else :
      result = ReportTestResult()
      if result == 0:
        print "TEST PASSED %s in %.1f seconds" % (test_name, time_taken / 1000)
            
      else:
        print "TEST FAILED %s in %.1f seconds" % (test_name, time_taken / 1000)

    print ""
    print "=" * 80
  print ""
except Exception, e:
  print "CATCH: %s" % e
  print FormatExceptionInfo()
  sys.exit(1)

sys.exit(result)

# End of onetest.py
