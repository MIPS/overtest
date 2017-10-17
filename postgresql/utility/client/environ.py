# -*- encoding: utf-8 -*-
# $Id: environ.py,v 1.6 2008/02/25 02:20:14 jwp Exp $
##
# copyright 2007, pg/python project.
# http://python.projects.postgresql.org
##
"""
PostgreSQL client environment configuration utilities

This project provides a relatively simple way to translate an environment
mapping into a more normalized connection configuration dictionary.

It's basic functionality is to simply map PG-environment to more generic
terms:

	PGUSER -> user
	PGDATABASE -> database
	PGHOST -> host
	PGHOSTADDR -> hostaddr
	PGPORT -> port
	PGPASSWORD -> password
	PGPASSFILE -> pgpassfile
	PGSSLMODE -> sslmode
	PGREALM -> kerberos4_realm
	PGKRBSVRNAME -> kerberos5_service

[Extensions]
	PGUNIX -> socket (path to unix file system socket)
	PGROLE -> role (role to set when connected)

These are a finite map with zero manipulation of the values.
However, the features don't end there.

It provides structured path values for setting the search_path prefix:

	PGPATH -> path (':' separated)

PGREQUIRESSL gets rewritten into "sslmode = 'require'".

PGSERVICE gets applied directly to the dictionary.

PGIRI gets applied first(standard environment overrides).
(See postgresql.utility.client.iri for more information on PGIRI)
"""
import os
import sys
import ConfigParser

from postgresql.utility.config import instance as pg_config
import postgresql.utility.client.iri as pg_iri
import postgresql.strings as pg_str

# Environment variables that require no transformation.
exact_map = {
	'PGUSER' : 'user',
	'PGDATABASE' : 'database',
	'PGHOST' : 'host',
	'PGHOSTADDR' : 'hostaddr',
	'PGPORT' : 'port',
	'PGOPTIONS' : 'options',
	'PGPASSWORD' : 'password',
	'PGPASSFILE' : 'pgpassfile',

	'PGSSLMODE' : 'sslmode',
	'PGSSLKEY' : 'sslkey',
	'PGGSSLIB' : 'gsslib',
	'PGREALM' : 'kerberos4_realm',
	'PGKRBSRVNAME' : 'kerberos5_service',

	'PGCONNECT_TIMEOUT' : 'connect_timeout',

	# Extensions
	'PGUNIX' : 'unix',
	'PGROLE' : 'role',
	#'PGPATH' : 'path',
}

pg_service_envvar = 'PGSERVICE'
pg_sysconfdir_envvar = 'PGSYSCONFDIR'
pg_servicefile_envvar = 'PGSERVICEFILE'
pg_service_filename = 'pg_service.conf'
def service_data(d, env):
	"""
	Lookup service data from the service file specified in ``env``.

	If PGSERVICEFILE is specified, use it.
	If PGSYSCONFDIR is specified, use it with `pg_service.conf` appended to it.
	Otherwise, lookup the ``sysconfdir`` from the first ``pg_config`` command
	found; append `pg_service.conf`.

	If no `pg_service.conf` file is found, a warning is thrown.
	"""
	if pg_service_envvar in env:
		# Need to resolve a PGSERVICE?
		service_file = env.get(pg_servicefile_envvar)
		if service_file is None:
			# No service file defined? look for PGSYSCONFDIR
			service_file = env.get(pg_sysconfdir_envvar)
			if service_file is None:
				# No PGSYSCONDIR enviornment, last ditch effort using pg_config.
				try:
					service_file = pg_config(
						env.get('PGCONFIG', 'pg_config'),
						validate = False
					).sysconfdir
				except:
					service_file = os.path.curdir

				warnings.warn(
					"unable to find appropriate pg_service.conf file " \
					"directory, using %r.(Set PGSYSCONFDIR to quiet this)" %(
						service_file,
					)
				)
			service_file = os.path.join(service_file, pg_service_filename)

		cp = ConfigParser.ConfigParser()
		fp = open(service_file)
		try:
			cp.readfp(fp, filename = service_file)
		finally:
			fp.close()

		try:
			items = cp.items(env[pg_service_envvar])
		except ConfigParser.NoSectionError:
			# nothing to do; consistent with libpq.
			return

		d.update(items)
		if 'dbname' in d:
			d.setdefault('database', d.pop('dbname'))

set_before = [
	('IRI', lambda d, env: d.update(pg_iri.parse(env.get('PGIRI',''))))
]

set_immediate = [
	# PGSSLMODE will override this in standard; REQUIRE_SSL being
	# deprecated, it seems natural for PGSSLMODE to supercede this.
	('REQUIRE_SSL', lambda d, env: (
			env.get('PGREQUIRESSL', '0') == '1'
		) and d.update([('sslmode', 'require')])
	),

	('STANDARD', lambda d, env: d.update([
		(v, env[k]) for k, v in exact_map.iteritems() if k in env
	])),
]

set_after = [
	('PGSERVICE', service_data)
]

set_sequence = [
	set_before,
	set_immediate,
	set_after
]

def convert_environ(env = os.environ, xseq = set_sequence):
	'given an environment, make a connection parameter dictionary'
	d = {}
	for s in xseq:
		for x, op in s:
			op(d, env)
	return d
