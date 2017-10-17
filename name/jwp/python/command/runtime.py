# -*- encoding: utf-8 -*-
# $Id: runtime.py 521 2008-05-30 00:23:55Z jwp $
##
# copyright 2007, James William Pye. http://jwp.name
##
"""
Provides the 'execution' class and the 'ExtendedConsole'.
"""
import os
import sys
import re
import code
from traceback import print_exception
try:
	import subprocess
except ImportError:
	pass
import name.jwp.python.command.loader as cmd_load

class ExtendedConsole(code.InteractiveConsole):
	"""
	Console subclass providing some convenient backslash commands.
	"""
	def __init__(self, *args, **kw):
		import tempfile
		self.mktemp = tempfile.mktemp
		import shlex
		self.split = shlex.split
		code.InteractiveConsole.__init__(self, *args, **kw)

		self.bsc_map = {}
		self.temp_files = {}
		self.past_buffers = []

		self.register_backslash(r'\?', self.showhelp, "Show this help message.")
		self.register_backslash(r'\set', self.bs_set,
			"Configure environment variables. \set without arguments to show all")
		self.register_backslash(r'\E', self.bs_E,
			"Edit a file or a temporary script.")
		self.register_backslash(r'\i', self.bs_i,
			"Execute a Python script within the interpreter's context.")
		self.register_backslash(r'\e', self.bs_e,
			"Edit and Execute the file directly in the context.")
		self.register_backslash(r'\x', self.bs_x,
			"Execute the Python command within this process.")

	def register_backslash(self, bscmd, meth, doc):
		self.bsc_map[bscmd] = (meth, doc)

	def execslash(self, line):
		"""
		If push() gets a line that starts with a backslash, execute
		the command that the backslash sequence corresponds to.
		"""
		cmd = line.split(None, 1)
		cmd.append('')
		bsc = self.bsc_map.get(cmd[0])
		if bsc is None:
			self.write("ERROR: unknown backslash command: %s%s"%(cmd, os.linesep))
		else:
			return bsc[0](cmd[0], cmd[1])

	def showhelp(self, cmd, arg):
		i = self.bsc_map.items()
		i.sort(lambda x, y: cmp(x[0],y[0]))
		helplines = os.linesep.join([
			'  %s%s%s' %(
				x[0], ' ' * (8 - len(x[0])), x[1][1]
			) for x in i
		])
		self.write("Backslash Commands:%s%s%s" %(
			os.linesep*2, helplines, os.linesep*2
		))

	def bs_set(self, cmd, arg):
		"""
		Set a value in the interpreter's environment.
		"""
		if arg:
			for x in self.split(arg):
				if '=' in x:
					k, v = x.split('=', 1)
					os.environ[k] = v
					self.write("%s=%s%s" %(k, v, os.linesep))
				elif x:
					self.write("%s=%s%s" %(x, os.environ.get(x, ''), os.linesep))
		else:
			for k,v in os.environ.iteritems():
				self.write("%s=%s%s" %(k, v, os.linesep))

	def resolve_path(self, path, dont_create = False):
		"""
		Get the path of the given string; if the path is not
		absolute and does not contain path separators, identify
		it as a temporary file.
		"""
		if not os.path.isabs(path) and not os.path.sep in path:
			# clean it up to avoid typos
			path = path.strip().lower()
			tmppath = self.temp_files.get(path)
			if tmppath is None:
				if dont_create is False:
					tmppath = self.mktemp(
						suffix = '.py',
						prefix = '_console_%s_' %(path,)
					)
					self.temp_files[path] = tmppath
				else:
					return path
			return tmppath
		return path

	def execfile(self, filepath):
		src = file(filepath)
		try:
			try:
				co = compile(src.read(), filepath, 'exec')
			except SyntaxError:
				co = None
				print_exception(*sys.exc_info())
		finally:
			src.close()
		if co is not None:
			try:
				exec co in self.locals
			except:
				e, v, tb = sys.exc_info()
				print_exception(e, v, tb.tb_next or tb)

	def editfiles(self, filepaths):
		sp = list(filepaths)
		sp.insert(0, os.environ.get('EDITOR', 'vi'))
		return subprocess.call(sp)

	def bs_i(self, cmd, arg):
		'edit the files, but *only* edit them'
		for x in self.split(arg) or ('',):
			p = self.resolve_path(x, dont_create = True)
			self.execfile(p)

	def bs_E(self, cmd, arg):
		'edit the files, but *only* edit them'
		self.editfiles([self.resolve_path(x) for x in self.split(arg) or ('',)])

	def bs_e(self, cmd, arg):
		'edit and execute the files'
		filepaths = [self.resolve_path(x) for x in self.split(arg) or ('',)]
		self.editfiles(filepaths)
		for x in filepaths:
			self.execfile(x)

	def bs_x(self, cmd, arg):
		rv = -1
		if len(cmd) > 1:
			a = self.split(arg)
			a.insert(0, '\\x')
			rv = command(args = a)
			self.write("[Return Value: %d]%s" %(rv, os.linesep))

	def push(self, line):
		# Has to be a ps1 context.
		if not self.buffer and line.startswith('\\'):
			try:
				self.execslash(line)
			except:
				# print the exception, but don't raise.
				e, v, tb = sys.exc_info()
				print_exception(e, v, tb.tb_next or tb)
		else:
			return code.InteractiveConsole.push(self, line)

class execution(object):
	"""
	Given argv, context, locals, environ, make an execution instance that,
	when called, will execute the Python configured code.

	This class provides the ability to identify what the main part of the
	execution of the configured Python code. For instance, shall it execute a
	console, the file that the first argument points to, a -m option module
	appended to the python_context option value, or the code given within -c?

	Primarily, it simply identifies what "__main__" is, while providing other
	conveniences such as postmortem.
	"""
	def __init__(self,
		args, context = (), main = None,
		postmortem = None, loader = None,
		stdin = sys.stdin
	):
		"""
		args
			The arguments passed to the script; usually sys.argv after being
			processed by optparse(ca).
		context
			A list of loader descriptors that will be used to establish the
			context of __main__ module.
		locals
			The dictionary that will be used for __main__.
		main
			Overload to explicitly state what main is. None will cause the
			class to attempt to fill in the attribute using 'args' and other
			system objects like sys.stdin.
		postmortem
			A object reference string(module path + .object). Usually set to
			'pdb.pm'. If 'None', by default, an exception raised by main will
			only cause an exception to be printed. When a reference string,
			the object that is being referenced with be called with no arguments.
		"""
		self.args = args
		self.context = context and list(context) or ()
		self.postmortem = postmortem

		if main is not None:
			self.main = main
		elif loader is not None:
			# Main explicitly stated, resolve the path and the loader
			path, ldesc = loader
			ltitle, rloader, xpath = ldesc
			l = rloader(path)
			if l is None:
				raise ImportError(
					"%s %r does not exist or cannot be read" %(
						ltitle, path
					)
				)
			self.main = (path, l)
		# If there are args, but no main, run the first arg.
		elif args:
			fp = self.args[0]
			f = file(fp)
			try:
				l = cmd_load.file_loader(fp, fileobj = f)
			finally:
				f.close()
			self.main = (self.args[0], l)
		# There is no main, no loader, and no args.
		# If stdin is not a tty, use stdin as the main file.
		elif not stdin.isatty():
			l = cmd_load.file_loader('<stdin>', fileobj = stdin)
			self.main = ('<stdin>', l)
		# tty and no "main".
		else:
			# console
			self.main = (None, None)

	def _call(self, locals = {}, console = ExtendedConsole,):
		"""
		Initialize the context and run main in the given locals
		(Note: tramples on sys.argv, __main__ in sys.modules)
		(Use __call__ instead)
		"""
		locals['__name__'] = '__context__'
		sys.modules['__context__'] = locals

		# Establish context in the locals
		for path, ldesc in self.context:
			ltitle, loader, xpath = ldesc
			rpath = xpath(path)
			li = loader(rpath)
			if li is None:
				sys.stderr.write(
					"%s %r does not exist or cannot be read%s" %(
						ltitle, rpath, os.linesep
					)
				)
				return 1
			try:
				code = li.get_code(rpath)
			except:
				print_exception(*sys.exc_info())
				return 1
			locals['__file__'] = getattr(
				li, 'get_filename', lambda x: x
			)(rpath)
			locals['__loader__'] = li
			try:
				exec code in locals
			except:
				e, v, tb = sys.exc_info()
				print_exception(e, v, tb.tb_next or tb)
				return 1

		sys.modules['__main__'] = locals
		locals['__name__'] = '__main__'
		if self.main == (None, None):
			sys.argv = self.args or ['<console>']
			try:
				import readline
			except ImportError:
				pass
			ic = console(locals = locals)
			try:
				ic.interact()
			except SystemExit, e:
				return e.code
			return 0
		else:
			path, loader = self.main
			locals['__file__'] = getattr(
				loader, 'get_filename', lambda x: x
			)(path)
			sys.argv = list(self.args)
			sys.argv.insert(0, locals['__file__'])
			try:
				code = loader.get_code(path)
			except:
				print_exception(*sys.exc_info())
				# Unlikely that the user wants to postmortem a sytaxerror.
				return 1
			rv = 0
			try:
				exec code in locals
			except SystemExit, e:
				rv = e.code
				e, v, tb = sys.exc_info()
				sys.last_traceback = (tb.tb_next or tb)
			except:
				rv = 1
				e, v, tb = sys.exc_info()
				print_exception(e, v, tb.tb_next or tb)
				sys.last_traceback = (tb.tb_next or tb)
			else:
				return rv
			if self.postmortem is not None:
				pm = self.postmortem.split('.')
				attr = pm.pop(-1)
				modpath = '.'.join(pm)
				m = __import__(modpath, fromlist = modpath)
				pmobject = getattr(m, attr, None)
				if pmobject is not None:
					try:
						pmobject()
					except:
						sys.stderr.write(
							"[Exception raised by Postmortem]" + os.linesep
						)
						print_exception(*sys.exc_info())
				else:
					sys.stderr.write(
						"ERROR: no object at %r for postmortem"%(
						postmortem
					))
			return rv

	def __call__(self, *args, **kw):
		storage = (
			sys.modules.get('__context__'),
			sys.modules.get('__main__'),
			sys.argv,
			os.environ,
		)
		try:
			os.environ = kw.pop('environ', None) or os.environ.copy()
			self.environ = os.environ
			return self._call(*args, **kw)
		finally:
			sys.modules['__context__'], \
			sys.modules['__main__'], \
			sys.argv, os.environ = storage

	def get_main_source(self):
		"""
		Get the execution's "__main__" source. Useful for configuring
		environmental options derived from "magic" lines.
		"""
		path, loader = self.main
		if path is not None:
			return loader.get_source(path)

def command_execution(args = sys.argv):
	'create an execution using the given args and environ'
	import optparse
	import name.jwp.python.command.option as cmd_option
	op = optparse.OptionParser(
		"%prog [options] [script] [script arguments]",
		version = '1.1.1',
	)
	op.disable_interspersed_args()
	op.add_options(cmd_option.default)
	co, ca = op.parse_args(args[1:])
	return execution(ca,
		context = getattr(co, 'python_context', ()),
		loader = getattr(co, 'python_main', None),
		postmortem = co.python_postmortem,
	)

def command(args = sys.argv, environ = os.environ, locals = {}):
	'run an execution using the given args and environ'
	pythonexec = command_execution(args = args)
	return pythonexec(
		locals = locals,
		environ = environ
	)

if __name__ == '__main__':
	raise SystemExit(command())
##
# vim: ts=3:sw=3:noet:
