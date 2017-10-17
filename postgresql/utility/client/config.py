# -*- encoding: utf-8 -*-
# $Id: config.py,v 1.2 2008/01/08 10:37:54 jwp Exp $
##
# copyright 2007, pg/python project.
# http://python.projects.postgresql.org
##
"""
client connection configuration dictionary constructor
"""
import sys
import os
import postgresql.utility.client.pgpass as pgpass
import postgresql.utility.client.environ as client_environ

try:
	from getpass import getuser, getpass
except ImportError:
	getpass = raw_input
	getuser = lambda: 'postgres'

default_host = 'localhost'
default_port = 5432
pg_home_passfile = '.pgpass'
pg_home_directory = '.postgresql'
pg_appdata_directory = 'postgresql'
pg_appdata_passfile = 'pgpass.conf'

def defaults(getuser = getuser, environ = {}, config = None):
	user = getuser()
	if sys.platform == 'win32':
		appdata = environ.get('APPDATA')
		if appdata:
			pgdata = os.path.join(environ.get('APPDATA'), pg_appdata_directory)
			passfile = os.path.join(pgdata, pg_appdata_passfile)
	else:
		userdir = os.path.expanduser('~' + user)
		passfile = os.path.join(userdir, pg_home_passfile)
		pgdata = os.path.join(pg_home_directory)

	# if they exist, they appear in the returned configuration
	files = [
		('sslcrtfile', os.path.join(pgdata, 'postgresql.crt')),
		('sslkeyfile', os.path.join(pgdata, 'postgresql.key')),
		('sslrootcrtfile', os.path.join(pgdata, 'root.crt')),
		('sslrootcrlfile', os.path.join(pgdata, 'root.crl')),
		('pgpassfile', passfile),
	]

	config = config or {}
	config.update({
		'user' : user,
		'host' : default_host,
		'port' : default_port,
	})
	config.update([
		x for x in files if os.path.exists(x[1])
	])
	return config

socket_providers = ('pipe', 'socket', 'unix', 'host', 'process',)
def merge_config(d, od):
	"""
	merge the second mapping onto the first using special rules
	to keep the integrity of the configuration dictionary.
	(split path, remove socket_providers when one is being merged)
	"""
	# Remove existing socket provider as it has been superceded.
	nd = dict(od)
	for k in nd:
		if k in socket_providers:
			for x in socket_providers:
				d.pop(x, None)
			break
	# However, let port persist in case host is specified in another merge.

	# Remove conflicts based on the positional priority(first one wins)
	win = None
	for x in socket_providers:
		if x in nd:
			if win is None:
				win = x
			else:
				del nd[x]

	# filter out the non-standard merges
	d.setdefault('settings', {}).update(dict(nd.pop('settings', {})))
	d['path'] = list(nd.pop('path', ())) + list(d.get('path', ()))
	dbname = nd.pop('dbname', None)
	if dbname is not None:
		d.setdefault('database', dbname)

	d.update([
		kv for kv in nd.iteritems() if kv[1] is not None
	])

optionmap = {
	'server_options' : 'options',
}
optionattr = [
	'user',
	'port',
	'database',
	'settings',
	'fragment',
	'sslmode',
	'role',
	'path',
]

def convert_options(co, attrlist = optionattr, attrmap = optionmap):
	"""
	Make a mapping sequence of pairs from an instance
	postgresql.utility.client.option's parsed options.
	"""
	for attname, key in attrmap.iteritems():
		v = getattr(co, attname, None)
		if v is not None:
			yield key, value
	for key in attrlist:
		v = getattr(co, key, None)
		if v is not None:
			yield key, v
	sp = getattr(co, 'socket_provider', None)
	if sp is not None:
		yield sp[0], sp[1]
		if sp[0] == 'host' and co.port:
			yield 'port', co.port

def convert_environ(environ):
	"""
	Convert output from postgresql.utility.client.environ.convert_environ
	to a GreenTrunk connection configuration dictionary.
	"""
	d = client_environ.convert_environ(environ)
	# FIXME: No escape for colons.
	path = d.pop('path', None)
	if path is not None:
		d['path'] = path.split(':')
	return d

def resolve_password(d):
	"""
	Given a dictionary containing 'password' and 'pgpassfile' keys
	"""
	if d.get('password') is None:
		passfile = d.get('pgpassfile')
		if passfile is not None:
			d['password'] = pgpass.lookup_pgpass(d, passfile)
	d.pop('pgpassfile', None)

def create(co, environ = os.environ, config = None):
	d = defaults(environ = environ, config = config)
	merge_config(d, convert_environ(environ))
	merge_config(d, convert_options(co))

	if co.prompt_password is True:
		if sys.stdin.isatty():
			d['password'] = getpass("Password for user %s: " %(
				d['user'],
			))
		else:
			# getpass will throw an exception if it's not a tty,
			pw = sys.stdin.readline()
			if pw.endswith(os.linesep):
				pw = pw[:len(pw)-len(os.linesep)]
			d['password'] = pw
	resolve_password(d)
	return d
