# -*- encoding: utf-8 -*-
# $Id: config.py,v 1.6 2008/05/20 02:35:27 jwp Exp $
##
# copyright 2005, pg/python project.
# http://python.projects.postgresql.org
##
'pg_config Python interface; provides member based access to pg_config data'
import os

try:
	import subprocess as sp
	def call(exe, *args):
		'helper function for the instance class'
		p = [
			'--' + x.strip() for x in args if x is not None
		]
		p.insert(0, exe)
		p = sp.Popen(p,
			stdout = sp.PIPE, stderr = sp.PIPE, stdin = sp.PIPE, shell = False)
		p.stdin.close()
		rv = p.wait()
		if rv != 0:
			return None
		return p.stdout.read()
except ImportError:
	from commands import getoutput
	def call(exe, *args):
		'helper function for the instance class'
		p = [
			'--' + x.strip() for x in args if x is not None
		]
		out = getoutput(exe + ' '.join(p))
		if out.startswith('pg_config: invalid argument:'):
			return None
		else:
			out = getoutput(exe)
		return out

def dictionary(pg_config_path):
	"""
	Create a dictionary of the information available in the given pg_config_path.
	This provides a one-shot solution to fetching information from the pg_config
	binary.
	"""
	default_output = call(pg_config_path)
	if default_output is not None:
		d = {}
		for x in call(pg_config_path).splitlines():
			if not x or x.isspace() or x.find('=') == -1:
				continue
			k, v = x.split('=', 1)
			# keep it semi-consistent with instance
			d[k.lower().strip()] = v.strip()
		return d

	# Support for 8.0 pg_config and earlier.
	# This requires three invocations of pg_config:
	#  First --help, to get the -- options available,
	#  Second, all the -- options except version.
	#  Third, --version as it appears to be exclusive.
	opt = []
	for l in call(pg_config_path, 'help').splitlines():
		dash_pos = l.find('--')
		if dash_pos == -1:
			continue
		sp_pos = l.find(' ', dash_pos)
		# the dashes are added by the call command
		opt.append(l[dash_pos+2:sp_pos])
	if 'help' in opt:
		opt.remove('help')
	if 'version' in opt:
		opt.remove('version')

	d=dict(zip(opt, call(pg_config_path, *opt).splitlines()))
	d['version'] = call(pg_config_path, 'version').strip()
	return d

class instance(object):
	"""
	instance([exe = 'pg_config'[, call = call[, validate = True]]])

	Create an instance of a pg_config executable. Access to the results are
	provided via attributes where dashes are replaced with underscores, and
	via the fetch method. (The fetch method does not reference a cache.)

	If validate is True(default), then instantiation will validate that the
	path is callable, so as to disallow an invalid instance.
	Setting validate to False will cause __init__ to continue initialization
	despite potential errors.

	Raises an OSError if the given path could not be validated.

	>>> from postgresql.utility.config import instance
	>>> i = instance(path_to_pg_config)
	>>> i.version
	'PostgreSQL 8.0.2'
	>>> i.pkglibdir
	'C:\\pgsql80\\lib'
	>>> i.includedir_server
	'/usr/local/include/postgresql/server'
	>>> i.pgxs
	'/usr/local/lib/postgresql/pgxs/src/makefiles/pgxs.mk'

	Use the 'dump' attribute to simulate a call without arguments. In normal
	cases, use of this is discouraged in favor of using the `dictionary`
	function.
	"""
	def __init__(self, exe = 'pg_config', call = call, validate = True):
		if validate:
			call(exe, 'version')

		self._exe = exe
		self._call = call

	def __repr__(self):
		return "<%s.%s '%s'>" %(self.__module__, type(self).__name__, self._exe,)

	def __str__(self):
		return self._exe

	def fetch(self, opt):
		'Get the results of the given option.(do not include the "--")'
		c = self._call
		if opt == 'dump':
			return c(self._exe, None)
		else:
			return c(self._exe, opt)

	def __getattr__(self, attr):
		if not attr.startswith('_') and attr != 'help':
			a = attr
			attr = '_pgc_' + attr + '_'
			if not hasattr(self, attr):
				opt = a.replace('_', '-')
				r = self.fetch(opt)
				if r is None:
					ae = AttributeError(
						"'%s' has no such option '--%s'"%(self._exe, opt,)
					)
					ae.path = self._exe
					ae.name = opt
					raise ae
				else:
					setattr(self, attr, r.strip())

		return super(instance, self).__getattribute__(attr)
