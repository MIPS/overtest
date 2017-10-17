# -*- encoding: utf-8 -*-
# $Id: test_query.py,v 1.3 2008/01/25 03:12:31 jwp Exp $
##
# copyright 2006, pg/python project.
# http://python.projects.postgresql.org
##
import unittest

class test_query(unittest.TestCase):
	def testNULL(self):
		# Directly commpare (SELECT NULL) is None
		self.failUnless(
			query("SELECT NULL")().next()[0] is None,
			"SELECT NULL did not return None"
		)
		# Indirectly compare (select NULL) is None
		self.failUnless(
			query("SELECT $1::text")(None).next()[0] is None,
			"[SELECT $1::text](None) did not return None "
		)

	def testBool(self):
		fst, snd = query("SELECT true, false")().next()
		self.failUnless(fst is True)
		self.failUnless(snd is False)

	def testSelect(self):
		self.failUnless(
			query('')() == None,
			'Empty query did not return None'
		)
		# Test SELECT 1.
		s1 = query("SELECT 1")
		p = s1()
		tup = p.next()
		self.failUnless(tup[0] == 1)

		for tup in s1:
			self.failUnless(tup[0] == 1)

	def testDDL(self):
		execute("CREATE TEMP TABLE t(i int)")
		try:
			insert_t = query("INSERT INTO t VALUES ($1)")
			delete_t = query("DELETE FROM t WHERE i = $1")
			delete_all_t = query("DELETE FROM t")
			update_t = query("UPDATE t SET i = $2 WHERE i = $1")
			self.failUnlessEqual(insert_t(1).count(), 1)
			self.failUnlessEqual(delete_t(1).count(), 1)
			self.failUnlessEqual(insert_t(2).count(), 1)
			self.failUnlessEqual(insert_t(2).count(), 1)
			self.failUnlessEqual(delete_t(2).count(), 2)

			self.failUnlessEqual(insert_t(3).count(), 1)
			self.failUnlessEqual(insert_t(3).count(), 1)
			self.failUnlessEqual(insert_t(3).count(), 1)
			self.failUnlessEqual(delete_all_t().count(), 3)

			self.failUnlessEqual(update_t(1, 2).count(), 0)
			self.failUnlessEqual(insert_t(1).count(), 1)
			self.failUnlessEqual(update_t(1, 2).count(), 1)
			self.failUnlessEqual(delete_t(1).count(), 0)
			self.failUnlessEqual(delete_t(2).count(), 1)
		finally:
			execute("DROP TABLE t")

	def testBatchDDL(self):
		execute("CREATE TEMP TABLE t(i int)")
		try:
			insert_t = query("INSERT INTO t VALUES ($1)")
			delete_t = query("DELETE FROM t WHERE i = $1")
			delete_all_t = query("DELETE FROM t")
			update_t = query("UPDATE t SET i = $2 WHERE i = $1")
			mset = (
				(2,), (2,), (3,), (4,), (5,),
			)
			insert_t << mset
			self.failUnlessEqual(mset, tuple([
				tuple(x) for x in query(
					"SELECT * FROM t ORDER BY 1 ASC"
				)
			]))
		finally:
			execute("DROP TABLE t")

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(this)
