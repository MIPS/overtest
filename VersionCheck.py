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
