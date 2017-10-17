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
