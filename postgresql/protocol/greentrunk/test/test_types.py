# -*- encoding: utf-8 -*-
# $Id: test_types.py,v 1.5 2008/05/29 21:26:12 jwp Exp $
##
# copyright 2006, pg/python project.
# http://python.projects.postgresql.org
##
import unittest
import datetime

samples = (
	('smallint', (
			((1 << 16) / 2) - 1, - ((1 << 16) / 2),
			-1, 0, 1,
		),
	),
	('int', (
			((1 << 32) / 2) - 1, - ((1 << 32) / 2),
			-1, 0, 1,
		),
	),
	('bigint', (
			((1 << 64) / 2) - 1, - ((1 << 64) / 2),
			-1, 0, 1,
		),
	),
	('bytea', (
			''.join([chr(x) for x in xrange(256)]),
			''.join([chr(x) for x in xrange(255, -1, -1)]),
		),
	),
	('smallint[]', (
			(123,321,-123,-321),
		),
	),
	('int[]', (
			(123,321,-123,-321),
		),
	),
	('bigint[]', (
			(0xFFFFFFFFFFFF, -0xFFFFFFFFFFFF),
		),
	),
	('varchar[]', (
			(u"foo", u"bar",),
			("foo", "bar",),
		),
	),
	('timestamp', (
			datetime.datetime(2000,1,1,5,25,10),
			datetime.datetime(500,1,1,5,25,10),
		),
	)
)

class test_types(unittest.TestCase):
	def testPassback(self):
		'test basic object I/O--input must equal output'
		for typname, sample_data in samples:
			pb = query("SELECT $1::" + typname)
			for sample in sample_data:
				rsample = pb.first(sample)
				self.failUnless(
					rsample == sample,
					"failed to return %s object data as-is; gave %r, received %r" %(
						typname, sample, rsample
					)
				)

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(module = this)
