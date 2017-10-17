#!/usr/bin/python
import VersionCheck

from OvtDB import OvtDB
import getopt
import signal
from utils.TerminalUtilities import *
from OvertestExceptions import *
from LogManager import LogManager
import resource
resource.setrlimit(resource.RLIMIT_CORE, (0,0))
(slimit, hlimit) = resource.getrlimit(resource.RLIMIT_STACK)
resource.setrlimit(resource.RLIMIT_STACK, (10485760,hlimit))

try:
  log = LogManager(None, True)
  ovtDB = OvtDB(log)
except Exception, e:
  print e
  print "Failed to connect to database"
  sys.exit(1)

def usage():
  print "Overtest Usage:"
  print "overtest -r --resource           Enter interactive resource management"
  print "overtest -p --prepare            Prepare actions and dependencies"
  print "overtest -h <host> --host=<host> Start the overtest daemon for <host>"
  print "overtest -g --gridhost	          Start the overtest execution engine for a testrun"
  print "overtest -a --allocate           Start the overtest allocator daemon"
  print "overtest -c --check              Start the overtest dependency checker daemon"
  print "overtest -m --monitor            Enter the test monitoring console"
  print "overtest -n --notify             Start the overtest notification daemon"
  print "overtest -s --submit             Submit a result for a testsuite"
  print "overtest -l --claim              Manage resource claims"
  print "overtest -t --testrun            Edit or create a testrun"
  print "overtest -d --gridsubmit         Submit jobs to a grid engine"
  print "overtest    --import             Import data from YAML files"
  print "overtest    --export             Export data from YAML files"
  print "overtest    --addon=<addon>      Run an addon"

if len(sys.argv) < 2:
  usage()
  sys.exit(2)

try:
  opts, args = getopt.getopt([sys.argv[1]], "rpghamncslidet",
			     ["resource","prepare","gridhost","host","allocate",
			      "monitor","notify","check","submit","claim","edit",
			      "testrun","gridsubmit","export","import","addon="])
except getopt.GetoptError, e:
  usage()
  sys.exit(2)

try:
  if len(opts) == 0:
    usage()
    sys.exit(2)
  (o,a) = opts[0]
  if o in ("-r", "--resource"):
    if len(sys.argv) <= 2:
      setupScreen()
    import ResourceControl
    r = ResourceControl.ResourceControl(ovtDB)
    exitcode = r.run(sys.argv[2:])
    sys.exit(exitcode)
  elif o in ("-p", "--prepare"):
    import TestPreparation
    p = TestPreparation.TestPreparation(ovtDB)
    p.run(sys.argv[2:])
    sys.exit(0)
  elif o in ("-h", "--host"):
    import Host
    n = Host.Host(ovtDB)
    n.run(sys.argv[2], sys.argv[3:])
    sys.exit(0)
  elif o in ("-g", "--gridhost"):
    import GridHost
    n = GridHost.GridHost(ovtDB)
    n.run(sys.argv[2:])
    sys.exit(0)
  elif o in ("-a", "--allocate"):
    setupScreen()
    import HostAllocator
    a = HostAllocator.HostAllocator(ovtDB)
    a.run()
    sys.exit(0)
  elif o in ("-c", "--check"):
    setupScreen()
    import DependencyCheck
    a = DependencyCheck.DependencyCheck(ovtDB)
    a.run()
    sys.exit(0)
  elif o in ("-m", "--monitor"):
    import TestMonitor
    a = TestMonitor.TestMonitor(ovtDB)
    a.run(sys.argv[2:])
    sys.exit(0)
  elif o in ("-n", "--notify"):
    import NotificationDaemon
    a = NotificationDaemon.NotificationDaemon(ovtDB)
    a.run()
    sys.exit(0)
  elif o in ("-l", "--claim"):
    # Prevent stopping a process. It may hold a database lock!
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    import ClaimManager
    a = ClaimManager.ClaimManager(ovtDB)
    if a.execute(sys.argv[2:]):
      sys.exit(0)
    else:
      sys.exit(1)
  elif o in ("-s", "--submit"):
    import ResultSubmission
    a = ResultSubmission.ResultSubmission(ovtDB)
    if a.execute(sys.argv[2:]):
      sys.exit(0)
    else:
      sys.exit(1)
  elif o in ("-e", "--edit", "-t", "--testrun"):
    import TestrunEditing
    a = TestrunEditing.TestrunEditing(ovtDB)
    a.execute(sys.argv[2:])
  elif o in ("-d", "--gridsubmit"):
    import GridSubmitter
    a = GridSubmitter.GridSubmitter(ovtDB)
    a.run(sys.argv[2:])
  elif o == "--export":
    import ImportExport
    a = ImportExport.ImportExport(ovtDB)
    sys.exit (a.exporter(sys.argv[2:]))
  elif o == "--import":
    import ImportExport
    a = ImportExport.ImportExport(ovtDB)
    sys.exit(a.importer(sys.argv[2:]))
  elif o == "--addon":
    exec("from addons.%s.Addon import Addon" % a)
    a = Addon(ovtDB)
    a.run(sys.argv[2:])
    sys.exit(0)
except SystemExit, e:
  # These are normal and should be passed straight through
  raise
except StartupException, e:
  # These are raised when initialising the modules
  print e
  sys.exit(1)
except Exception, e:
  # These should not happen!
  print e
  print formatExceptionInfo()
  sys.exit(1)




