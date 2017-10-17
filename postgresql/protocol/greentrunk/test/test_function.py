# -*- encoding: utf-8 -*-
# $Id: test_function.py,v 1.3 2008/01/25 03:12:31 jwp Exp $
##
# copyright 2006, pg/python project.
# http://python.projects.postgresql.org
##
import unittest

class aspects(unittest.TestCase):
	def testLookupByName(self):
		execute(
			"CREATE OR REPLACE FUNCTION public.foo() RETURNS INT LANGUAGE SQL AS 'SELECT 1'"
		)
		settings['search_path'] = 'public'
		f = proc('foo()')
		f2 = proc('public.foo()')
		self.failUnless(f.oid == f2.oid,
			"function lookup incongruence(%r != %r)" %(f, f2)
		)

	def testLookupById(self):
		pass

	def testExecution(self):
		ver = proc("version()")
		ver()
		execute(
			"CREATE OR REPLACE FUNCTION ifoo(int) RETURNS int LANGUAGE SQL AS 'select $1'"
		)
		ifoo = proc('ifoo(int)')
		self.failUnless(ifoo(1) == 1)
		self.failUnless(ifoo(None) is None)

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(this)
