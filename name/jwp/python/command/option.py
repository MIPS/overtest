# -*- encoding: utf-8 -*-
# $Id: option.py 495 2008-01-03 23:53:28Z jwp $
##
# copyright 2007, James William Pye. http://jwp.name
##
"""
Python command options.

There are only three. --python-context (pre-main code to be executed),
--python-postmortem (object to call when an exception is raised), -m (module to
execute), and -c (single command to run).

-m and -c use a callback to initialize their value. Primarily, this is done to
signal the OptionParser that no more options should be parsed. It sends the
signal by INSERTING '--' INTO THE ARGUMENTS LIST PASSED INTO THE parse_args()
METHOD. While this appears to work, it is certainly very hacky, so be warned
about the actions these options may take. Notably, it will do this *iff* the
parser is not allowing interspersed arguments (not allow_interspersed_args).
If allow_interspersed_args is enabled, the python_main value may be overwritten
by subsequent options using the set_python_main() callback.
"""
from gettext import gettext as _
from optparse import make_option
import name.jwp.python.command.loader as cmd_load

def append_context(option, opt_str, value, parser):
	"""
	Add some context to the execution of the Python code using
	loader module's directory list of loader descriptions.

	If no loader can be found, assume it's a Python command.
	"""
	pc = getattr(parser.values, option.dest, None) or []
	if not pc:
		setattr(parser.values, option.dest, pc)
	ldesc = cmd_load.find_loader(value)
	if ldesc is None:
		ldesc = cmd_load.single_loader_descriptor
	pc.append((value, ldesc))

def set_python_main(option, opt_str, value, parser):
	"""
	Set the main Python code; after contexts are initialized, main is ran.
	"""
	main = (value, option.python_loader)
	setattr(parser.values, option.dest, main)
	# only terminate parsing if not interspersing arguments
	if not parser.allow_interspersed_args:
		parser.rargs.insert(0, '--')

python_context = make_option(
	'--python-context',
	help = _('Python context code to run[file://,module:,<code>(__context__)]'),
	dest = 'python_context',
	action = 'callback',
	callback = append_context,
	type = 'str'
)

module = make_option(
	'-m',
	help = _('Python module to run as script(__main__)'),
	dest = 'python_main',
	action = 'callback',
	callback = set_python_main,
	type = 'str'
)
module.python_loader = cmd_load.module_loader_descriptor

command = make_option(
	'-c',
	help = _('Python expression to run(__main__)'),
	dest = 'python_main',
	action = 'callback',
	callback = set_python_main,
	type = 'str'
)
command.python_loader = cmd_load.single_loader_descriptor

postmortem = make_option(
	'--python-postmortem',
	dest = 'python_postmortem',
	help = _('Execute the specified function after a fatal exception'),
	default = None,
)
pdb_pm = make_option(
	'--pdb-pm',
	dest = 'python_postmortem',
	help = _('Postmortem using pdb.pm'),
	action = 'store_const',
	const = 'pdb.pm'
)

default = [
	python_context,
	module,
	command,
	postmortem,
	pdb_pm
]
