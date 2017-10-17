# -*- encoding: utf-8 -*-
# $Id: python.py,v 1.4.2.1 2008/09/26 23:58:55 jwp Exp $
##
# copyright 2007, pg/python project.
# http://python.projects.postgresql.org
##
import sys
import os
import optparse
import postgresql.utility.client.option as pg_opt
import postgresql.utility.client.config as cl_config
import postgresql.protocol.greentrunk.python as gt_python
import postgresql.interface.proboscis.greentrunk as pg

pq_trace = optparse.make_option(
	'--pq-trace',
	dest = 'pq_trace',
	help = 'trace PQ protocol transmissions',
	default = None,
)
default_options = gt_python.default_options + [
	pq_trace,
]

def command(args, environ = os.environ):
	# Allow connection options to be collected in #!pb_python lines
	p = pg_opt.DefaultParser(
		"%prog [connection options] [script] [-- script options] [args]",
		version = '1.0.4',
		option_list = default_options
	)
	p.enable_interspersed_args()
	co, ca = p.parse_args(args[1:])

	cond = cl_config.create(co, environ = environ)
	connector = pg.connector(**cond)
	connection = connector.create()

	trace_file = None
	if co.pq_trace is not None:
		trace_file = open(co.pq_trace, 'a')
	try:
		if trace_file is not None:
			connection.tracer = trace_file.write
		return gt_python.run(
			connection, ca, co,
			in_xact = co.in_xact,
			environ = environ
		)
	finally:
		if trace_file is not None:
			trace_file.close()

def main():
	sys.exit(command(sys.argv))

if __name__ == '__main__':
	sys.exit(command(sys.argv))
##
# vim: ts=3:sw=3:noet:
