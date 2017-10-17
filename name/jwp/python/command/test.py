# -*- encoding: utf-8 -*-
# $Id: test.py 495 2008-01-03 23:53:28Z jwp $
##
# copyright 2007, James William Pye. http://jwp.name
##
'test option and runtime'
import sys
import os
import os.path
import optparse
import unittest
import tempfile
import name.jwp.python.command.option as cmd_opt
import name.jwp.python.command.runtime as cmd_rt
import name.jwp.python.command.loader as cmd_load

class Dead(Exception):
	pass

class DeadConsole(object):
	def __init__(self, *args, **kw):
		raise Dead('console')

class test_python_command_loader(unittest.TestCase):
	'Check features of the loader module'

	def testDirectory(self):
		'Test the default find_loader'
		self.failUnlessEqual(
			cmd_load.find_loader('foo', dir = cmd_load._directory),
			None
		)
		self.failUnlessEqual(
			cmd_load.find_loader('file://', dir = cmd_load._directory),
			cmd_load.file_loader_descriptor
		)
		self.failUnlessEqual(
			cmd_load.find_loader('module:', dir = cmd_load._directory),
			cmd_load.module_loader_descriptor
		)
		self.failUnlessEqual(
			cmd_load.find_loader('module:foo', dir = cmd_load._directory),
			cmd_load.module_loader_descriptor
		)
		self.failUnlessEqual(
			cmd_load.find_loader('file://foo', dir = cmd_load._directory),
			cmd_load.file_loader_descriptor
		)
		# again without the directory being specified
		self.failUnlessEqual(
			cmd_load.find_loader('file://foo'),
			cmd_load.file_loader_descriptor
		)

	def testSingleLoader(self):
		g = locals()
		def settrue():
			g['SingleLoaderShouldSetTrue'] = True
		src = 'settrue()'
		l = cmd_load.single_loader(src)
		# None when request is made for something that the
		# loader was not initialized with; mostly to support
		# the facets that are exhibited by other loader interfaces.
		self.failUnlessEqual(l.get_code('bar'), None)
		self.failUnlessEqual(l.get_source('bar'), None)
		self.failUnlessEqual(l.get_filename('bar'), None)

		self.failUnlessEqual(l.get_filename(src), '<command>')
		self.failUnlessEqual(l.get_source(src), src)
		eval(l.get_code(src), locals())
		self.failUnlessEqual(g['SingleLoaderShouldSetTrue'], True)

	def testScriptLoader(self):
		src = "raise OverflowError"
		tmp = tempfile.mktemp()
		f=file(tmp, 'w')
		f.write(src)
		f.close()
		l = cmd_load.file_loader(tmp)
		self.failUnlessEqual(l.get_code('bar'), None)
		self.failUnlessEqual(l.get_source('bar'), None)
		self.failUnlessEqual(l.get_filename('bar'), None)

		self.failUnlessEqual(l.get_filename(tmp), tmp)
		self.failUnlessEqual(l.get_source(tmp), src)
		self.failUnlessRaises(
			OverflowError, eval, l.get_code(tmp)
		)

	def testModuleLoader(self):
		src = "raise OverflowError"
		tmp = tempfile.mktemp('.py')
		f=file(tmp, 'w')
		f.write(src)
		f.close()
		tmpc = tmp + 'c'
		tmpo = tmp + 'o'
		d = os.path.dirname(tmp)
		bn = os.path.basename(tmp)
		modname = bn[:-3]
		spath = sys.path
		try:
			# put the temp's directory in the path
			sys.path = list(sys.path)
			sys.path.append(d)
			l = cmd_load.module_loader(modname)
			self.failUnlessRaises(ImportError, l.get_code, 'bar')
			self.failUnlessRaises(ImportError, l.get_source, 'bar')
			self.failUnlessRaises(ImportError, l.get_filename, 'bar')
			self.failUnlessRaises(
				OverflowError, eval, l.get_code(modname)
			)
			self.failUnlessEqual(
				src, l.get_source(modname)
			)
		finally:
			sys.path = spath
			if os.path.exists(tmpc):
				os.unlink(tmpc)
			if os.path.exists(tmpo):
				os.unlink(tmpo)

class test_python_command_options(unittest.TestCase):
	"""
	Check features of the option module.
	"""
	def setUp(self):
		self.op = optparse.OptionParser("test", cmd_opt.default)

	def testAppendContext(self):
		ctxts = [
			('from foo import bar', cmd_load.single_loader_descriptor),
			('file:///foo', cmd_load.file_loader_descriptor),
			('bleh', cmd_load.single_loader_descriptor),
		]
		co, ca = self.op.parse_args(
			['--python-context=' + x[0] for x in ctxts] + ['postoption']
		)
		self.failUnlessEqual(list(ca), ['postoption'])
		self.failUnlessEqual(co.python_context, ctxts)

	def testModuleMain(self):
		co, ca = self.op.parse_args(
			['-mfoo']
		)
		self.failUnlessEqual(
			co.python_main, ('foo', cmd_load.module_loader_descriptor)
		)

	def testCommandMain(self):
		co, ca = self.op.parse_args(
			['-cprint "foo"']
		)
		self.failUnlessEqual(
			co.python_main, ('print "foo"', cmd_load.single_loader_descriptor)
		)

	def testMainTermination(self):
		self.op.allow_interspersed_args = False
		co, ca = self.op.parse_args(
			['-cprint "foo"', '--bleh']
		)
		self.failUnlessEqual(
			co.python_main, ('print "foo"', cmd_load.single_loader_descriptor)
		)
		self.failUnlessEqual(ca, ['--bleh'])

		co, ca = self.op.parse_args(
			['-m', 'foo', '--bleh']
		)
		self.failUnlessEqual(ca, ['--bleh'])

	def testMainWithoutTermination(self):
		self.op.allow_interspersed_args = True
		co, ca = self.op.parse_args(
			['-m', 'foo', '--python-context=module:bar']
		)
		self.failUnlessEqual(ca, [])
		self.failUnlessEqual(
			co.python_main, ('foo', cmd_load.module_loader_descriptor)
		)
		self.failUnlessEqual(
			co.python_context,
			[('module:bar', cmd_load.module_loader_descriptor)]
		)

	def testPdbPM(self):
		co, ca = self.op.parse_args(
			['--pdb-pm']
		)
		self.failUnless(co.python_postmortem == 'pdb.pm')

	def testPM(self):
		co, ca = self.op.parse_args(
			['--python-postmortem=foobar']
		)
		self.failUnless(co.python_postmortem == 'foobar')

class test_python_command_runtime(unittest.TestCase):
	"""
	Check features of the runtime module.
	"""
	tmpsrc = """
num = %d
txt = %r
if not 'noraise' in dir():
	raise SystemExit(%d)"""

	def setUp(self):
		self.syspath = sys.path
		self.tmp = tempfile.mktemp(suffix = '.py')
		self.num = 1
		self.txt = 'foo'
		self.rv = 50
		self.src = self.tmpsrc %(self.num, self.txt, self.rv,)
		f=file(self.tmp, 'w')
		try:
			f.write(self.src)
		finally:
			f.close()
		sys.path = list(sys.path)
		sys.path.append(
			os.path.dirname(self.tmp),
		)
		self.tmpmodname = os.path.basename(self.tmp)[:-3]

	def tearDown(self):
		sys.path = self.syspath
		os.unlink(self.tmp)
		tmpc = self.tmp + 'c'
		tmpo = self.tmp + 'o'
		if os.path.exists(tmpc):
			os.unlink(tmpc)
		if os.path.exists(tmpo):
			os.unlink(tmpo)

	def std(self, pyexec, console = False, noraise = False, mainsrc = None):
		if mainsrc is None:
			mainsrc = self.src
		locals = {}
		if console:
			self.failUnlessRaises(
				Dead, pyexec, locals = locals,
				console = DeadConsole
			)
		else:
			rv = pyexec(locals = locals, console = DeadConsole)
			if noraise is True:
				self.failUnlessEqual(rv, 0)
			else:
				self.failUnlessEqual(rv, self.rv)
			self.failUnlessEqual(pyexec.get_main_source(), mainsrc)
		self.failUnlessEqual(locals['num'], 1)
		self.failUnlessEqual(locals['txt'], 'foo')
		return locals

	def testMainExecution(self):
		tl = cmd_load.file_loader(self.tmp)
		pyexec = cmd_rt.execution(
			[], main = (self.tmp, tl)
		)
		self.std(pyexec)

	def testLoaderExecution(self):
		pyexec = cmd_rt.execution(
			[], loader = (self.tmp, cmd_load.file_loader_descriptor)
		)
		self.std(pyexec)

	def testArgExecution(self):
		pyexec = cmd_rt.execution(
			[self.tmp],
		)
		self.std(pyexec)
	
	def testMainWithArg(self):
		tl = cmd_load.file_loader(self.tmp)
		pyexec = cmd_rt.execution(
			['foobar.py'], main = (self.tmp, tl)
		)
		self.std(pyexec)

	def testStdinExecution(self):
		f = file(self.tmp)
		try:
			pyexec = cmd_rt.execution([], stdin = file(self.tmp))
		finally:
			f.close()
		self.std(pyexec)
	
	def testConsole(self):
		pyexec = cmd_rt.execution([])
		self.failUnlessRaises(Dead, pyexec, console = DeadConsole)
		pyexec = cmd_rt.execution([], context = [
			('foo=1', cmd_load.single_loader_descriptor)
		])
		l = {}
		self.failUnlessRaises(Dead, pyexec, locals = l, console = DeadConsole)
		self.failUnlessEqual(l['foo'], 1)
		pyexec = cmd_rt.execution([], context = [
			('noraise=1', cmd_load.single_loader_descriptor),
			('file://' + self.tmp, cmd_load.file_loader_descriptor)
		])
		self.std(pyexec, console = True)

	def testExecutionWithContext(self):
		mainsrc = 'nothing="something"'
		pyexec = cmd_rt.execution([], context = [
				('noraise=1', cmd_load.single_loader_descriptor),
				('file://' + self.tmp, cmd_load.file_loader_descriptor)
			],
			main = (
				mainsrc, cmd_load.single_loader(mainsrc)
			)
		)
		l = self.std(pyexec, noraise = True, mainsrc = mainsrc)
		self.failUnlessEqual(l['nothing'], "something")

		# using module:
		pyexec = cmd_rt.execution([], context = [
				('noraise=1', cmd_load.single_loader_descriptor),
				('module:' + self.tmpmodname, cmd_load.module_loader_descriptor)
			],
			main = (
				mainsrc, cmd_load.single_loader(mainsrc)
			)
		)
		l = self.std(pyexec, noraise = True, mainsrc = mainsrc)
		self.failUnlessEqual(l['nothing'], "something")

	def testCommand(self):
		pyexec = cmd_rt.command_execution(['test', self.tmp])
		self.std(pyexec)
		pyexec = cmd_rt.command_execution(['test',
			'--python-context=attr=2',
			'--python-context=attr2="foo"',
			self.tmp
		])
		l = self.std(pyexec)
		self.failUnlessEqual(
			l['attr'], 2,
			"expecting 'attr' to be set by the first context"
		)
		self.failUnlessEqual(
			l['attr2'], 'foo',
			"expecting 'attr2' to be set by the second context"
		)

		mainsrc = 'nothing="something"'
		pyexec = cmd_rt.command_execution(['test',
			'--python-context=noraise=1',
			'--python-context=module:' + self.tmpmodname,
			'-c', mainsrc
		])
		l = self.std(pyexec, noraise = True, mainsrc = mainsrc)
		self.failUnlessEqual(l['nothing'], "something")

		# and again, but as a file
		pyexec = cmd_rt.command_execution(['test',
			'--python-context=noraise=1',
			'--python-context=file://' + self.tmp,
			'-c', mainsrc
		])
		l = self.std(pyexec, noraise = True, mainsrc = mainsrc)
		self.failUnlessEqual(l['nothing'], "something")

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(this)
