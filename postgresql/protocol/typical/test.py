# -*- encoding: utf-8 -*-
# $Id: test.py,v 1.1 2008/01/05 21:01:18 jwp Exp $
##
# Copyright 2007, pg/python project.
# http://python.projects.postgresql.org
##
import unittest
import postgresql.protocol.typical.oidmaps as oidmaps
import postgresql.types as pg_type

# this must pack to that, and
# that must unpack to this
expectation_samples = {
	pg_type.BOOLOID : [
		(True, '\x01'),
		(False, '\x00')
	],

	pg_type.INT2OID : [
		(0, '\x00\x00'),
		(1, '\x00\x01'),
		(2, '\x00\x02'),
		(0x0f, '\x00\x0f'),
		(0xf00, '\x0f\x00'),
		(0x7fff, '\x7f\xff'),
		(-0x8000, '\x80\x00'),
		(-1, '\xff\xff'),
		(-2, '\xff\xfe'),
		(-3, '\xff\xfd'),
	],

	pg_type.INT4OID : [
		(0, '\x00\x00\x00\x00'),
		(1, '\x00\x00\x00\x01'),
		(2, '\x00\x00\x00\x02'),
		(0x0f, '\x00\x00\x00\x0f'),
		(0x7fff, '\x00\x00\x7f\xff'),
		(-0x8000, '\xff\xff\x80\x00'),
		(0x7fffffff, '\x7f\xff\xff\xff'),
		(-0x80000000, '\x80\x00\x00\x00'),
		(-1, '\xff\xff\xff\xff'),
		(-2, '\xff\xff\xff\xfe'),
		(-3, '\xff\xff\xff\xfd'),
	],

	pg_type.INT8OID : [
		(0, '\x00\x00\x00\x00\x00\x00\x00\x00'),
		(1, '\x00\x00\x00\x00\x00\x00\x00\x01'),
		(2, '\x00\x00\x00\x00\x00\x00\x00\x02'),
		(0x0f, '\x00\x00\x00\x00\x00\x00\x00\x0f'),
		(0x7fffffff, '\x00\x00\x00\x00\x7f\xff\xff\xff'),
		(0x80000000, '\x00\x00\x00\x00\x80\x00\x00\x00'),
		(-0x80000000, '\xff\xff\xff\xff\x80\x00\x00\x00'),
		(-1, '\xff\xff\xff\xff\xff\xff\xff\xff'),
		(-2, '\xff\xff\xff\xff\xff\xff\xff\xfe'),
		(-3, '\xff\xff\xff\xff\xff\xff\xff\xfd'),
	],

	pg_type.BITOID : [
		(False, '\x00\x00\x00\x01\x00'),
		(True, '\x00\x00\x00\x01\x01'),
	],

	pg_type.VARBITOID : [
		((0, '\x00'), '\x00\x00\x00\x00\x00'),
		((1, '\x01'), '\x00\x00\x00\x01\x01'),
		((1, '\x00'), '\x00\x00\x00\x01\x00'),
		((2, '\x00'), '\x00\x00\x00\x02\x00'),
		((3, '\x00'), '\x00\x00\x00\x03\x00'),
		((9, '\x00\x00'), '\x00\x00\x00\x09\x00\x00'),
		# More data than necessary, we allow this.
		# Let the user do the necessary check if the cost is worth the benefit.
		((9, '\x00\x00\x00'), '\x00\x00\x00\x09\x00\x00\x00'),
	],

	pg_type.BYTEAOID : [
		('foo', 'foo'),
		('bar', 'bar'),
		('\x00', '\x00'),
		('\x01', '\x01'),
	],

	pg_type.CHAROID : [
		('a', 'a'),
		('b', 'b'),
		('\x00', '\x00'),
	],

	pg_type.MACADDROID : [
		('abcdef', 'abcdef'),
		('fedcba', 'fedcba')
	],

	pg_type.POINTOID : [
		((1.0, 1.0), '?\xf0\x00\x00\x00\x00\x00\x00?\xf0\x00\x00\x00\x00\x00\x00'),
		((2.0, 2.0), '@\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00'),
		((-1.0, -1.0),
			'\xbf\xf0\x00\x00\x00\x00\x00\x00\xbf\xf0\x00\x00\x00\x00\x00\x00'),
	],

	pg_type.CIRCLEOID : [
		((1.0, 1.0, 1.0),
			'?\xf0\x00\x00\x00\x00\x00\x00?\xf0\x00\x00' \
			'\x00\x00\x00\x00?\xf0\x00\x00\x00\x00\x00\x00'),
		((2.0, 2.0, 2.0),
			'@\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00' \
			'\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00'),
	],

	pg_type.RECORDOID : [
		([], '\x00\x00\x00\x00'),
		([(0,'foo')], '\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x03foo'),
		([(0,None)], '\x00\x00\x00\x01\x00\x00\x00\x00\xff\xff\xff\xff'),
		([(15,None)], '\x00\x00\x00\x01\x00\x00\x00\x0f\xff\xff\xff\xff'),
		([(0xffffffff,None)], '\x00\x00\x00\x01\xff\xff\xff\xff\xff\xff\xff\xff'),
		([(0,None), (1,'some')],
		 '\x00\x00\x00\x02\x00\x00\x00\x00\xff\xff\xff\xff' \
		 '\x00\x00\x00\x01\x00\x00\x00\x04some'),
	],

	pg_type.ANYARRAYOID : [
		([0, 0xf, (1, 0), ('foo',)],
			'\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x0f\x00\x00\x00\x01' \
			'\x00\x00\x00\x00\x00\x00\x00\x03foo'
		),
		([0, 0xf, (1, 0), (None,)],
			'\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x0f\x00\x00\x00\x01' \
			'\x00\x00\x00\x00\xff\xff\xff\xff'
		)
	],
}
expectation_samples[pg_type.BOXOID] = \
	expectation_samples[pg_type.LSEGOID] = [
		((1.0, 1.0, 1.0, 1.0),
			'?\xf0\x00\x00\x00\x00\x00\x00?\xf0' \
			'\x00\x00\x00\x00\x00\x00?\xf0\x00\x00' \
			'\x00\x00\x00\x00?\xf0\x00\x00\x00\x00\x00\x00'),
		((2.0, 2.0, 1.0, 1.0),
			'@\x00\x00\x00\x00\x00\x00\x00@\x00\x00' \
			'\x00\x00\x00\x00\x00?\xf0\x00\x00\x00\x00' \
			'\x00\x00?\xf0\x00\x00\x00\x00\x00\x00'),
		((-1.0, -1.0, 1.0, 1.0),
			'\xbf\xf0\x00\x00\x00\x00\x00\x00\xbf\xf0' \
			'\x00\x00\x00\x00\x00\x00?\xf0\x00\x00\x00' \
			'\x00\x00\x00?\xf0\x00\x00\x00\x00\x00\x00'),
	]

expectation_samples[pg_type.OIDOID] = \
	expectation_samples[pg_type.CIDOID] = \
	expectation_samples[pg_type.XIDOID] = [
		(0, '\x00\x00\x00\x00'),
		(1, '\x00\x00\x00\x01'),
		(2, '\x00\x00\x00\x02'),
		(0xf, '\x00\x00\x00\x0f'),
		(0xffffffff, '\xff\xff\xff\xff'),
		(0x7fffffff, '\x7f\xff\xff\xff'),
	]

# this must pack and then unpack back into this
consistency_samples = {
	pg_type.BOOLOID : [True, False],

	pg_type.RECORDOID : [
		[],
		[(0,'foo')],
		[(0,None)],
		[(15,None)],
		[(0xffffffff,None)],
		[(0,None), (1,'some')],
		[(0,None), (1,'some'), (0xffff, 'something_else\x00')],
		[(0,None), (1,'s\x00me'), (0xffff, '\x00something_else\x00')],
	],

	pg_type.ANYARRAYOID : [
		[0, 0xf, (), ()],
		[0, 0xf, (0, 0), ()],
		[0, 0xf, (1, 0), ('foo',)],
		[0, 0xf, (1, 0), (None,)],
		[0, 0xf, (2, 0), (None,None)],
		[0, 0xf, (2, 0), ('foo',None)],
		[0, 0xff, (2, 0), (None,'foo',)],
		[0, 0xffffffff, (3, 0), (None,'foo',None)],
		[1, 0xffffffff, (3, 0), (None,'foo',None)],
		[1, 0xffffffff, (3, 0, 1, 0), (None,'foo',None)],
		[1, 0xffffffff, (3, 0, 2, 0), (None,'one','foo','two',None,'three')],
	],

	# Just some random data; it's just an integer, so nothing fancy.
	pg_type.DATEOID : [
		123,
		321,
		0x7FFFFFF,
		-0x8000000,
	],

	pg_type.TIMETZOID : [
		((0, 0), 0),
		((123, 123), 123),
		((0xFFFFFFFF, 999999), -123),
	],

	pg_type.POINTOID : [
		(0, 0),
		(2, 2),
		(-1, -1),
		(-1.5, -1.2),
		(1.5, 1.2),
	],

	pg_type.CIRCLEOID : [
		(0, 0, 0),
		(2, 2, 2),
		(-1, -1, -1),
		(-1.5, -1.2, -1.8),
	],

	pg_type.TIDOID : [
		(0, 0),
		(1, 1),
		(0xffffffff, 0xffff),
		(0, 0xffff),
		(0xffffffff, 0),
		(0xffffffff / 2, 0xffff / 2),
	],

	pg_type.CIDROID : [
		(0, 0, '\x00\x00\x00\x00'),
		(2, 0, '\x00' * 4),
		(3, 0, '\x00\x00' * 16),
	],

	pg_type.INETOID : [
		'\x00\x00\x00\x00',
		'\x7f\x00\x00\x01',
		'\xff\x00\xff\x01',
		'\x7f\x00' * 16,
		'\xff\xff' * 16,
		'\x00\x00' * 16,
	],
}

consistency_samples[pg_type.TIMEOID] = \
consistency_samples[pg_type.TIMESTAMPOID] = \
consistency_samples[pg_type.TIMESTAMPTZOID] = [
	(0, 0),
	(123, 123),
	(0xFFFFFFFF, 999999),
]

# months, days, (seconds, microseconds)
consistency_samples[pg_type.INTERVALOID] = [
	(0, 0, (0, 0)),
	(1, 0, (0, 0)),
	(0, 1, (0, 0)),
	(1, 1, (0, 0)),
	(0, 0, (0, 10000)),
	(0, 0, (1, 0)),
	(0, 0, (1, 10000)),
	(1, 1, (1, 10000)),
	(100, 50, (1423, 29313))
]

consistency_samples[pg_type.OIDOID] = \
	consistency_samples[pg_type.CIDOID] = \
	consistency_samples[pg_type.XIDOID] = [
	0, 0xffffffff, 0xffffffff / 2, 123, 321, 1, 2, 3
]

consistency_samples[pg_type.LSEGOID] = \
	consistency_samples[pg_type.BOXOID] = [
	(1,2,3,4),
	(4,3,2,1),
	(0,0,0,0),
	(-1,-1,-1,-1),
	(-1.2,-1.5,-2.0,4.0)
]

consistency_samples[pg_type.PATHOID] = \
	consistency_samples[pg_type.POLYGONOID] = [
	(1,2,3,4),
	(4,3,2,1),
	(0,0,0,0),
	(-1,-1,-1,-1),
	(-1.2,-1.5,-2.0,4.0)
]



# need the generator type for arrays' element_ pack and unpack
def g():
	yield 1
gtype = type(g())

def resolve(ob):
	'make sure generators get "tuplified"'
	if type(ob) not in (list, tuple, gtype):
		return ob
	return [resolve(x) for x in ob]

def testExpectIO(self, map, samples):
	for oid, sample in samples.iteritems():
		for (sample_unpacked, sample_packed) in sample:
			pack, unpack = map[oid]

			pack_trial = pack(sample_unpacked)
			self.failUnless(
				pack_trial == sample_packed,
				"%s sample: unpacked sample, %r, did not match " \
				"%r when packed, rather, %r" %(
					pg_type.oid_to_name[oid], sample_unpacked,
					sample_packed, pack_trial
				)
			)

			sample_unpacked = resolve(sample_unpacked)
			unpack_trial = resolve(unpack(sample_packed))
			self.failUnless(
				unpack_trial == sample_unpacked,
				"%s sample: packed sample, %r, did not match " \
				"%r when unpacked, rather, %r" %(
					pg_type.oid_to_name[oid], sample_packed,
					sample_unpacked, unpack_trial
				)
			)

class typio(unittest.TestCase):
	def testExpectations(self):
		'IO tests where the pre-made expected serialized form is compared'
		testExpectIO(self, oidmaps.stdio, expectation_samples)

	def testConsistency(self):
		'IO tests where the unpacked source is compared to re-unpacked result'
		for oid, sample in consistency_samples.iteritems():
			pack, unpack = oidmaps.stdio.get(oid, (None, None))
			if pack is not None:
				for x in sample:
					packed = pack(x)
					unpacked = resolve(unpack(packed))
					x = resolve(x)
					self.failUnless(x == unpacked,
						"inconsistency with %s, %r -> %r -> %r" %(
							pg_type.oid_to_name[oid],
							x, packed, unpacked
						)
					)
		for oid, (pack, unpack) in oidmaps.time_io.iteritems():
			sample = consistency_samples.get(oid, [])
			for x in sample:
				packed = pack(x)
				unpacked = resolve(unpack(packed))
				x = resolve(x)
				self.failUnless(x == unpacked,
					"inconsistency with %s, %r -> %r -> %r" %(
						pg_type.oid_to_name[oid],
						x, packed, unpacked
					)
				)

		for oid, (pack, unpack) in oidmaps.time64_io.iteritems():
			sample = consistency_samples.get(oid, [])
			for x in sample:
				packed = pack(x)
				unpacked = resolve(unpack(packed))
				x = resolve(x)
				self.failUnless(x == unpacked,
					"inconsistency with %s, %r -> %r -> %r" %(
						pg_type.oid_to_name[oid],
						x, packed, unpacked
					)
				)

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(this)
