# -*- encoding: utf-8 -*-
# $Id: test_exceptions.py,v 1.4 2008/01/27 04:39:41 jwp Exp $
##
# copyright 2006, pg/python project.
# http://python.projects.postgresql.org
##
import unittest
import postgresql.exceptions as pg_exc

class aspects(unittest.TestCase):
	def testExistence(self):
		pass
	
	def testTraps(self):
		pass
	
	def testSyntaxError(self):
		self.failUnlessRaises(
			pg_exc.SyntaxError,
			query, "SELEKT 1",
		)
	
	def testInvalidSchemaError(self):
		self.failUnlessRaises(
			pg_exc.InvalidSchemaName,
			query, "SELECT * FROM sdkfldasjfdskljZknvson.foo"
		)
	
	def testUndefinedTableError(self):
		self.failUnlessRaises(
			pg_exc.UndefinedTableError,
			query, "SELECT * FROM public.lkansdkvsndlvksdvnlsdkvnsdlvk"
		)

	def testUndefinedColumnError(self):
		self.failUnlessRaises(
			pg_exc.UndefinedColumnError,
			query, "SELECT x____ysldvndsnkv FROM information_schema.tables"
		)

	def testSEARVError_avgInWhere(self):
		self.failUnlessRaises(
			pg_exc.SEARVError,
			query, "SELECT 1 WHERE avg(1) = 1"
		)
	
	def testSEARVError_groupByAgg(self):
		self.failUnlessRaises(
			pg_exc.SEARVError,
			query, "SELECT 1 GROUP BY avg(1)"
		)
	
	def testDatatypeMismatchError(self):
		self.failUnlessRaises(
			pg_exc.DatatypeMismatchError,
			query, "SELECT 1 WHERE 1"
		)

	def testUndefinedObjectError(self):
		try:
			self.failUnlessRaises(
				pg_exc.UndefinedObjectError,
				query, "CREATE TABLE lksvdnvsdlksnv(i intt___t)"
			)
		except:
			# newer versions throw the exception on execution
			self.failUnlessRaises(
				pg_exc.UndefinedObjectError,
				query("CREATE TABLE lksvdnvsdlksnv(i intt___t)")
			)

	def testZeroDivisionError(self):
		self.failUnlessRaises(
			pg_exc.ZeroDivisionError,
			query("SELECT 1/i FROM (select 0 as i) AS g(i)").first,
		)

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(this)
