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
#
# Simple redirect wrapper that enabled any script in overtest to be
# invoked via the python interpreter change in VersionCheck.
# The module to invoke is specified as a relative import from the root
# of overtest such as addons.p4_autobuild.scheduler
# The folder containing the module is added to the python path to allow
# relative imports in the top level script to work.
# argv is 'fixed' as if no redirection had occurred.
#

import VersionCheck

import sys
import os

sys.argv = sys.argv[1:]
mod = sys.argv[0]
components = mod.split(".")

sys.path.append(os.path.join(sys.path[0], os.sep.join(components[:-1])))

exec("import %s" % mod)
