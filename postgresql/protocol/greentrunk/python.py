# -*- encoding: utf-8 -*-
# $Id: python.py,v 1.3 2008/01/25 03:12:31 jwp Exp $
##
# copyright 2007, pg/python project.
# http://python.projects.postgresql.org
##
'provisions for making a Python command with a Postgres connection'
import os
import sys
import re
import code
import name.jwp.python.command.runtime as cmd_rt
import name.jwp.python.command.option as cmd_opt
import postgresql.utility.client.option as pg_opt

default_options = [
	pg_opt.in_xact,
] + cmd_opt.default

class SavingConsole(cmd_rt.ExtendedConsole):
	def __init__(self, *args, **kw):
		cmd_rt.ExtendedConsole.__init__(self, *args, **kw)
		self.autosave = False
		self.register_backslash('\\s', self.toggle_autosave,
			"Wrap each execution code of in a new SAVEPOINT; Rollback on exception"
		)

	def toggle_autosave(self, cmd, arg):
		if self.autosave:
			self.autosave = False
			self.write("[Automatic savepointing Disabled]" + os.linesep)
		else:
			if gtx.xact.closed:
				gtx.xact.start()
			elif gtx.xact.failed:
				gtx.xact.reset()
				gtx.xact.start()
			self.autosave = True
			self.write("[Automatic savepointing Enabled]" + os.linesep)

	def runcode(self, codeob):
		if self.autosave:
			return self.runsavedcode(codeob)
		else:
			return cmd_rt.ExtendedConsole.runcode(self, codeob)

	def runsavedcode(self, codeob):
		try:
			try:
				if not gtx.closed:
					gtx.xact.start()
			except:
				self.showtraceback()
				exec codeob in self.locals
			else:
				try:
					exec codeob in self.locals
				except SystemExit, e:
					if not gtx.closed:
						if e.code == 0:
							gtx.xact.commit()
						else:
							gtx.xact.abort()
					raise
				except:
					if not gtx.closed:
						gtx.xact.abort()
					raise
				else:
					if not gtx.closed:
						gtx.xact.commit()
		except SystemExit:
			raise
		except:
			self.showtraceback()

gt_param_pattern = re.compile(
	ur'^\s*#\s+-\*-\s+greentrunk\.([^:]+):\s+([^\s]*)\s+-\*-\s*$',
	re.M
)
def extract_parameters(src):
	'extract hard parameters out of the "-*- greentrunk.*: -*-" magic lines'
	return [
		x for x in re.findall(gt_param_pattern, src)
	]

def run(
	connection, ca, co, in_xact = False, environ = os.environ
):
	pythonexec = cmd_rt.execution(ca,
		context = getattr(co, 'python_context', None),
		loader = getattr(co, 'python_main', None),
		postmortem = co.python_postmortem,
	)
	builtin_overload = {
		'gtc' : connection.connector,
		'gtx' : connection,
		'query' : connection.query,
		'cquery' : connection.cquery,
		'statement' : connection.statement,
		'execute' : connection.execute,
		'settings' : connection.settings,
		'cursor' : connection.cursor,
		'proc' : connection.proc,
		'xact' : connection.xact,
	}
	__builtins__.update(builtin_overload)

	# Some points of configuration need to be demanded by a script.
	src = pythonexec.get_main_source()
	if src is not None:
		hard_params = dict(extract_parameters(src))
		if hard_params:
			if hard_params.get('disconnected', 'false') != 'true':
				connection.connect()
			else:
				in_xact = False

			iso = hard_params.get('isolation')
			if iso is not None:
				if iso == 'none':
					in_xact = False
				else:
					in_xact = True
					connection.xact(isolation = iso)
		else:
			connection.connect()
	else:
		connection.connect()

	try:
		if in_xact is True:
			connection.xact.start()
		try:
			rv = pythonexec(
				console = SavingConsole,
				environ = environ
			)
		except:
			if in_xact is True:
				connection.xact.abort()
			raise
		if in_xact is True:
			if rv == 0:
				connection.xact.commit()
			else:
				connection.xact.abort()
	finally:
		connection.close()
		for x in builtin_overload.iterkeys():
			del __builtins__[x]
	return rv
##
# vim: ts=3:sw=3:noet:
