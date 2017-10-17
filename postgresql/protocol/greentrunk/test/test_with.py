# -*- encoding: utf-8 -*-
# $Id: test_with.py,v 1.3 2008/05/30 02:49:15 jwp Exp $
##
# copyright 2006, pg/python project.
# http://python.projects.postgresql.org
##
from __future__ import with_statement
import unittest
import postgresql.exceptions as pg_exc

class testWith(unittest.TestCase):
	def testTransaction(self):
		with xact:
			execute("CREATE TEMP TABLE withfoo(i int)")
		query("SELECT * FROM withfoo")

		execute("DROP TABLE withfoo")
		with xact:
			execute("CREATE TEMP TABLE withfoo(i int)")
			raise pg_exc.AbortTransaction
		self.failUnlessRaises(
			pg_exc.UndefinedTableError,
			query, "SELECT * FROM withfoo"
		)

		class SomeError(StandardError):
			pass
		try:
			with xact:
				execute("CREATE TABLE withfoo (i int)")
				raise SomeError
		except SomeError:
			pass
		self.failUnlessRaises(
			pg_exc.UndefinedTableError,
			query, "SELECT * FROM withfoo"
		)
	
	def testConfiguredTransaction(self):
		if 'gid' in xact.prepared:
			xact.rollback_prepared('gid')
		with xact('gid'):
			pass
		with xact:
			pass
		xact.rollback_prepared('gid')

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(this)
