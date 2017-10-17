import sys
from Config import CONFIG
import os
if 'LD_LIBRARY_PATH' in os.environ:
  libpath = os.environ['LD_LIBRARY_PATH'].split(":")
  while libpath.count("") > 0:
    libpath.remove("")
  os.environ['LD_LIBRARY_PATH'] = ":".join(libpath)
if not sys.executable in [CONFIG.python, CONFIG.python_exe]:
  script = sys.argv.pop(0)
  sys.argv.insert(0, os.path.join(sys.path[0], os.path.basename(script)))
  sys.argv.insert(0, CONFIG.python)

  os.execv(CONFIG.python, sys.argv)
  # Terminates

if sys.version_info[0] != 2 \
   or sys.version_info[1] != 7:
  sys.stderr.write("Incorrect version of python installed at: %s\n" % CONFIG.python)
  sys.exit(10)
