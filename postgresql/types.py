# -*- encoding: utf-8 -*-
# $Id: types.py,v 1.9 2008/03/18 21:53:13 jwp Exp $
##
# copyright 2007, pg/python project.
# http://python.projects.postgresql.org
##
'PostgreSQL types and identifiers'
import struct
import socket
import math

InvalidOid = 0

RECORDOID = 2249
BOOLOID = 16
BITOID = 1560
VARBITOID = 1562
ACLITEMOID = 1033

CHAROID = 18
NAMEOID = 19
TEXTOID = 25
BYTEAOID = 17
BPCHAROID = 1042
VARCHAROID = 1043
CSTRINGOID = 2275
UNKNOWNOID = 705
REFCURSOROID = 1790
UUIDOID = 2950

TSVECTOROID = 3614
GTSVECTOROID = 3642
TSQUERYOID = 3615
REGCONFIGOID = 3734
REGDICTIONARYOID = 3769

XMLOID = 142

MACADDROID = 829
INETOID = 869
CIDROID = 650

TYPEOID = 71
PROCOID = 81
CLASSOID = 83
ATTRIBUTEOID = 75

DATEOID = 1082
TIMEOID = 1083
TIMESTAMPOID = 1114
TIMESTAMPTZOID = 1184
INTERVALOID = 1186
TIMETZOID = 1266
ABSTIMEOID = 702
RELTIMEOID = 703
TINTERVALOID = 704

INT8OID = 20
INT2OID = 21
INT4OID = 23
OIDOID = 26
TIDOID = 27
XIDOID = 28
CIDOID = 29
CASHOID = 790
FLOAT4OID = 700
FLOAT8OID = 701
NUMERICOID = 1700

POINTOID = 600
LINEOID = 628
LSEGOID = 601
PATHOID = 602
BOXOID = 603
POLYGONOID = 604
CIRCLEOID = 718

OIDVECTOROID = 30
INT2VECTOROID = 22
INT4ARRAYOID = 1007

REGPROCOID = 24
REGPROCEDUREOID = 2202
REGOPEROID = 2203
REGOPERATOROID = 2204
REGCLASSOID = 2205
REGTYPEOID = 2206
REGTYPEARRAYOID = 2211

TRIGGEROID = 2279
LANGUAGE_HANDLEROID = 2280
INTERNALOID = 2281
OPAQUEOID = 2282
VOIDOID = 2278
ANYARRAYOID = 2277
ANYELEMENTOID = 2283
ANYOID = 2276
ANYNONARRAYOID = 2776
ANYENUMOID = 3500


oid_to_name = {
	RECORDOID : 'record',
	BOOLOID : 'bool',
	BITOID : 'bit',
	VARBITOID : 'varbit',
	ACLITEMOID : 'aclitem',

	CHAROID : 'char',
	NAMEOID : 'name',
	TEXTOID : 'text',
	BYTEAOID : 'bytea',
	BPCHAROID : 'bpchar',
	VARCHAROID : 'varchar',
	CSTRINGOID : 'cstring',
	UNKNOWNOID : 'unknown',
	REFCURSOROID : 'refcursor',
	UUIDOID : 'uuid',

	TSVECTOROID : 'tsvector',
	GTSVECTOROID : 'gtsvector',
	TSQUERYOID : 'tsquery',
	REGCONFIGOID : 'regconfig',
	REGDICTIONARYOID : 'regdictionary',

	XMLOID : 'xml',

	MACADDROID : 'macaddr',
	INETOID : 'inet',
	CIDROID : 'cidr',

	TYPEOID : 'type',
	PROCOID : 'proc',
	CLASSOID : 'class',
	ATTRIBUTEOID : 'attribute',

	DATEOID : 'date',
	TIMEOID : 'time',
	TIMESTAMPOID : 'timestamp',
	TIMESTAMPTZOID : 'timestamptz',
	INTERVALOID : 'interval',
	TIMETZOID : 'timetz',
	ABSTIMEOID : 'abstime',
	RELTIMEOID : 'reltime',
	TINTERVALOID : 'tinterval',

	INT8OID : 'int8',
	INT2OID : 'int2',
	INT4OID : 'int4',
	OIDOID : 'oid',
	TIDOID : 'tid',
	XIDOID : 'xid',
	CIDOID : 'cid',
	CASHOID : 'cash',
	FLOAT4OID : 'float4',
	FLOAT8OID : 'float8',
	NUMERICOID : 'numeric',

	POINTOID : 'point',
	LINEOID : 'line',
	LSEGOID : 'lseg',
	PATHOID : 'path',
	BOXOID : 'box',
	POLYGONOID : 'polygon',
	CIRCLEOID : 'circle',

	OIDVECTOROID : 'oidvector',
	INT2VECTOROID : 'int2vector',
	INT4ARRAYOID : 'int4array',

	REGPROCOID : 'regproc',
	REGPROCEDUREOID : 'regprocedure',
	REGOPEROID : 'regoper',
	REGOPERATOROID : 'regoperator',
	REGCLASSOID : 'regclass',
	REGTYPEOID : 'regtype',
	REGTYPEARRAYOID : 'regtypearray',

	TRIGGEROID : 'trigger',
	LANGUAGE_HANDLEROID : 'language_handler',
	INTERNALOID : 'internal',
	OPAQUEOID : 'opaque',
	VOIDOID : 'void',
	ANYARRAYOID : 'anyarray',
	ANYELEMENTOID : 'anyelement',
	ANYOID : 'any',
	ANYNONARRAYOID : 'anynonarray',
	ANYENUMOID : 'anyenum',
}

name_to_oid = dict(
	[(v,k) for k,v in oid_to_name.iteritems()]
)
del k, v


def int2(ob):
	'overflow check for int2'
	return -0x8000 <= ob < 0x8000

def int4(ob):
	'overflow check for int4'
	return -0x80000000 <= ob < 0x80000000

def int8(ob):
	'overflow check for int8'
	return -0x8000000000000000 <= rob < 0x8000000000000000

def oid(ob):
	'overflow check for oid'
	return 0 <= ob <= 0xFFFFFFFF

def byte_to_bits(byte):
	v = ord(byte)
	return '%s%s%s%s%s%s%s%s' %(
		v & (1 << 7) and '1' or '0',
		v & (1 << 6) and '1' or '0',
		v & (1 << 5) and '1' or '0',
		v & (1 << 4) and '1' or '0',
		v & (1 << 3) and '1' or '0',
		v & (1 << 2) and '1' or '0',
		v & (1 << 1) and '1' or '0',
		v & 1 and '1' or '0',
	)

class varbit(object):
	def from_bits(subtype, bits, data):
		if bits == 1:
			return ord(data[0]) & (1 << 7) and OneBit or ZeroBit
		else:
			rob = object.__new__(subtype)
			rob.bits = bits
			rob.data = data
			return rob
	from_bits = classmethod(from_bits)

	def __new__(subtype, data):
		bits = len(data)
		nbytes, remain = divmod(bits, 8)
		bytes = [chr(int(data[x:x+8], 2)) for x in xrange(0, bits - remain, 8)]
		if remain != 0:
			bytes.append(chr(int(data[nbytes*8:].ljust(8,'0'), 2)))
		return subtype.from_bits(bits, ''.join(bytes))

	def __str__(self):
		if self.bits:
			# cut off the remainder from the bits
			blocks = [byte_to_bits(x) for x in self.data]
			blocks[-1] = blocks[-1][0:(self.bits % 8) or 8]
			return ''.join(blocks)
		else:
			return ''

	def __repr__(self):
		return '%s.%s(%r)' %(
			type(self).__module__,
			type(self).__name__,
			str(self)
		)

	def __len__(self):
		return self.bits

	def __add__(self, ob):
		return varbit(str(self) + str(ob))
	
	def __mul__(self, ob):
		return varbit(str(self) * ob)

	def getbit(self, bitoffset):
		if bitoffset < 0:
			idx = self.bits + bitoffset
		else:
			idx = bitoffset
		if not 0 <= idx < self.bits:
			raise IndexError("bit index %d out of range" %(bitoffset,))

		byte, bitofbyte = divmod(idx, 8)
		if ord(self.data[byte]) & (1 << (7 - bitofbyte)):
			return OneBit
		else:
			return ZeroBit

	def __getitem__(self, item):
		if isinstance(item, slice):
			return type(self)(str(self)[item])
		else:
			return self.getbit(item)

	def __nonzero__(self):
		for x in self.data:
			if x != '\x00':
				return True
		return False

class bit(varbit):
	def __new__(subtype, ob):
		if ob is False or ob == '0':
			return ZeroBit
		elif ob is True or ob == '1':
			return OneBit

		raise ValueError('unknown bit value %r, 0 or 1')

	def __nonzero__(self):
		return self is OneBit

	def __str__(self):
		return self is OneBit and '1' or '0'

	def __unicode__(self):
		return self is OneBit and u'1' or u'0'

ZeroBit = object.__new__(bit)
ZeroBit.data = '\x00'
ZeroBit.bits = 1
OneBit = object.__new__(bit)
OneBit.data = '\x80'
OneBit.bits = 1

class macaddr(object):
	"""
	An ethernet card hardware address. '08:00:2b:01:02:03'

	http://www.postgresql.org/docs/current/static/datatype-net-types.html#DATATYPE-MACADDR

	>>> macaddr('08:00:2b:01:02:03')
	postgresql.types.macaddr('08:00:2b:01:02:03')

	The properties `a`-`f` provide access to the bytes of the address.
	"""
	a = property(fget = lambda s: ord(s.data[0]))
	b = property(fget = lambda s: ord(s.data[1]))
	c = property(fget = lambda s: ord(s.data[2]))
	d = property(fget = lambda s: ord(s.data[3]))
	e = property(fget = lambda s: ord(s.data[4]))
	f = property(fget = lambda s: ord(s.data[5]))

	def from_data(subtype, data):
		rob = object.__new__(subtype)
		rob.data = data
		return rob
	from_data = classmethod(from_data)

	def from_int(subtype, i):
		return subtype.from_data(
			struct.pack("!LH", i >> 16, i & 0xFFFF) 
		)
	from_int = classmethod(from_int)

	def __new__(subtype, data):
		if data.count(':') != 5:
			raise ValueError('invalid value count for macaddr, six required')

		six = [int(x, base = 16) for x in data.split(':')]
		for x in six:
			if x > 255 or x < 0:
				raise ValueError('item %d out of range (%d)' %(six.index(x), x))
		return subtype.from_data(''.join([chr(x) for x in six]))

	def __int__(self):
		high, low = struct.unpack("!LH", self.data)
		return (high << 16) | low

	def __str__(self):
		return '%02x:%02x:%02x:%02x:%02x:%02x' % tuple([
			ord(x) for x in self.data
		])

	def __repr__(self):
		return '%s.%s(%r)' %(
			type(self).__module__,
			type(self).__name__,
			str(self),
		)

	def __hash__(self):
		return hash(self.data)

	def __getitem__(self, item):
		if isinstance(item, slice):
			return [ord(x) for x in self.data[item]]

		return ord(self.data[item])

	def __len__(self):
		return 6

	def __eq__(self, op, ob):
		return self.data.__eq__(type(self)(ob).data)

	def __gt__(self, op, ob):
		return self.data.__gt__(type(self)(ob).data)

	def __ge__(self, op, ob):
		return self.data.__ge__(type(self)(ob).data)

	def __lt__(self, op, ob):
		return self.data.__lt__(type(self)(ob).data)

	def __le__(self, op, ob):
		return self.data.__le__(type(self)(ob).data)

	def trunc(self):
		rdata = self.data[:3] + '\x00\x00\x00'
		rob = object.__new__(type(self))
		rob.data = rdata
		return rob

class inet(object):
	"""
	An IPv4 or IPv6 address. No mask.

	http://www.postgresql.org/docs/current/static/datatype-net-types.html#DATATYPE-INET
	"""

	family = property(
		fget = lambda s: len(s) == 4 and socket.AF_INET or socket.AF_INET6
	)
	familyname = property(
		fget = lambda s: len(s) == 4 and 'inet' or 'inet6'
	)

	def classvalue(idx, mknum = ord):
		def fget(self):
			return mknum(s.data[idx])
		doc = "get the ordinal value the data at %r" %(idx,)
		return dict(fget = fget, doc = doc)
	A = property(**classvalue(0))
	B = property(**classvalue(1))
	C = property(**classvalue(2))
	D = property(**classvalue(3))
	del classvalue

	def from_data(subtype, data):
		rob = object.__new__(subtype)
		rob.data = data
		return rob
	from_data = classmethod(from_data)

	def __new__(subtype, address_data):
		family = ':' in address_data and socket.AF_INET6 or socket.AF_INET
		data = socket.inet_pton(family, address_data)
		return subtype.from_data(data)

	def __hash__(self):
		return hash(self.data)

	def masked_int(self, mask):
		"""
		An integer of the masked version of the inet object.

		>>> n = inet('0.0.0.1')
		>>> n.masked(0)
		1
		>>> n.masked(1)
		0
		"""
		bits = len(self) * 8
		return (int(self) & ((1 << mask)-1 << (bits-mask)))

	def masked(self, mask):
		"""
		An inet instance with the given mask applied.

		>>> n = inet('127.0.0.1')
		>>> n.masked(16)
		inet('127.0.0.0')
		"""
		return type(self)(self.masked_int(mask))

	def inet_data(family, address):
		if family == socket.AF_INET6:
			high = address >> 64
			low = address & (0xffffffffffffffff)
			return struct.pack("!QQ", high, low)
		elif family == socket.AF_INET:
			return struct.pack("!L", address)
		else:
			raise TypeError("unknown family %d" %(family,))
	inet_data = staticmethod(inet_data)

	def from_number(subtype, family, address):
		rob = object.__new__(subtype)
		rob.data = subtype.inet_data(family, address)
		return rob
	from_number = classmethod(from_number)

	def max(subtype, family, **kw):
		'return the max inet instance for the given address family'
		if family in (socket.AF_INET6, 'inet6'):
			return subtype.from_number(
				family, 0xffffffffffffffffffffffffffffffff, **kw
			)
		elif family in (socket.AF_INET, 'inet'):
			return subtype.from_number(
				family, 0xffffffff, **kw
			)
		else:
			raise TypeError("unsupported address family %d" %(family,))
	max = classmethod(max)

	def __int__(self):
		if self.family == socket.AF_INET:
			return struct.unpack("!L", self.data)[0]
		elif self.family == socket.AF_INET6:
			high, low = struct.unpack("!QQ", self.data)
			return (high << 64) | low
		else:
			raise TypeError("unknown family %d" %(family,))

	def __add__(self, ob):
		return self.from_number(self.family, int(self) + ob)

	def __sub__(self, ob):
		return self + (- ob)

	def __str__(self):
		return socket.inet_ntop(self.family, self.data)

	def __repr__(self):
		return '%s.%s(%r)' %(
			type(self).__module__,
			type(self).__name__,
			str(self),
		)

	def __len__(self):
		return len(self.data)

class cidr(inet):
	"""
	A CIDR network address. This can be either a IPv4 or IPv6 address;
	this type attempts to provide an equivalent to the PostgreSQL ``cidr`` type.

	Basically, an IPv4 or IPv6 address with a mask. ::1/128, 127.0.0.1/32

	http://www.postgresql.org/docs/current/static/datatype-net-types.html#DATATYPE-CIDR

	>>> cidr('192.168.1.1/16')
	postgresql.types.cidr('192.168.1.1/16')
	>>> cidr('::1/128')
	postgresql.types.cidr('::1/128')
	"""

	def mask():
		fget = lambda s: s._mask
		def fset(self, value):
			mask = int(value)
			f = self.family
			if (
				(f == socket.AF_INET and (mask < 0 or mask > 32)) or
				(f == socket.AF_INET6 and (mask < 0 or mask > 128))
			):
				raise ValueError("invalid mask for CIDR address")
			self._mask = mask
			doc = "The cidr's network mask in bits masked"
		return locals()
	mask = property(**mask())

	def from_data_mask(subtype, data, mask):
		rob = object.__new__(subtype)
		rob.data = data
		rob.mask = mask or 0
		return rob
	from_data_mask = classmethod(from_data_mask)

	def from_number(subtype, family, address, mask = None):
		data = subtype.inet_data(family, address)
		return subtype.from_data(data, mask or 0)
	from_number = classmethod(from_number)

	def __new__(subtype, address_data, mask = None):
		pdata = address_data.split('/', 1)
		rob = inet.__new__(subtype, pdata[0])
		if len(pdata) == 1:
			rob.mask = mask or 0
		else:
			rob.mask = pdata[1] or mask or 0
		return rob

	def __hash__(self):
		return hash((self.data, rob._mask))

	def __str__(self):
		return '%s/%d' % (inet.__str__(self), self._mask)

	def __contains__(self, net):
		"""
		Checks if the given inet address is in the cidr network.

		>>> inet('127.0.0.1') in cidr('127.0.0.1/32')
		True
		>>> inet('127.0.0.1') in cidr('127.0.0.2/32')
		False
		>>> inet('127.0.0.1') in cidr('127.0.0.2/16')
		True
		"""
		return net.masked_int(self.mask) == self.masked_int()

	def masked_int(self, mask = None):
		"""
		Mask the address with the given integer(`mask`). If `mask` is not given,
		use the cidr object's ``mask`` attribute.

		>>> cidr('127.0.0.2/32').masked_int(16)
		"""
		if mask is None:
			mask = self._mask
		bits = len(self) * 8
		return (int(self) & ((1 << mask)-1 << (bits-mask)))

	def masked(self, mask = None):
		"""
		Return a new cidr object
		"""
		if mask is None:
			mask = self._mask
		return self.from_number(self.family, self.masked_int(mask), mask)

# Geometric types

class point(tuple):
	"""
	A point; a pair of floating point numbers.
	"""
	x = property(fget = lambda s: s[0])
	y = property(fget = lambda s: s[1])

	def __new__(subtype, pair):
		return tuple.__new__(subtype, (float(pair[0]), float(pair[1])))

	def __repr__(self):
		return '%s.%s(%s)' %(
			type(self).__module__,
			type(self).__name__,
			tuple.__repr__(self),
		)
	
	def __str__(self):
		return tuple.__repr__(self)

	def __add__(self, ob):
		wx, wy = ob
		return type(self)((self[0] + wx, self[1] + wy))

	def __sub__(self, ob):
		wx, wy = ob
		return type(self)((self[0] - wx, self[1] - wy))

	def __mul__(self, ob):
		wx, wy = ob
		rx = (self[0] * wx) - (self[1] * wy)
		ry = (self[0] * wy) + (self[1] * wx)
		return type(self)((rx, ry))

	def __div__(self, ob):
		sx, sy = self
		wx, wy = ob
		div = (wx * wx) + (wy * wy)
		rx = ((sx * wx) + (sy * wy)) / div
		ry = ((wx * sy) + (wy * sx)) / div
		return type(self)((rx, ry))

	def distance(self, ob):
		wx, wy = ob
		dx = self[0] - float(wx)
		dy = self[1] - float(wy)
		return math.sqrt(dx**2 + dy**2)

class lseg(tuple):
	one = property(fget = lambda s: s[0])
	two = property(fget = lambda s: s[1])

	length = property(fget = lambda s: s[0].distance(s[1]))
	vertical = property(fget = lambda s: s[0][0] == s[1][0])
	horizontal = property(fget = lambda s: s[0][1] == s[1][1])
	slope = property(
		fget = lambda s: (s[1][1] - s[0][1]) / (s[1][0] - s[0][0])
	)
	center = property(
		fget = lambda s: point((
			(s[0][0] + s[1][0]) / 2.0,
			(s[0][1] + s[1][1]) / 2.0,
		))
	)

	def __new__(subtype, pair):
		p1, p2 = pair
		return tuple.__new__(subtype, (point(p1), point(p2)))

	def __repr__(self):
		# Avoid the point representation
		return '%s.%s(%s, %s)' %(
			type(self).__module__,
			type(self).__name__,
			tuple.__repr__(self[0]),
			tuple.__repr__(self[1]),
		)

	def __str__(self):
		return '[(%s,%s),(%s,%s)]' %(
			self[0][0],
			self[0][1],
			self[1][0],
			self[1][1],
		)

	def parallel(self, ob):
		return self.slope == type(self)(ob).slope

	def intersect(self, ob):
		raise NotImplementedError

	def perpendicular(self, ob):
		return (self.slope / type(self)(ob).slope) == -1.0

class box(tuple):
	"""
	A pair of points. One specifying the top-right point of the box; the other
	specifying the bottom-left. `high` being top-right; `low` being bottom-left.

	http://www.postgresql.org/docs/current/static/datatype-geometric.html

	>>> box(( (0,0), (-2, -2) ))
	postgresql.types.box(((0.0, 0.0), (-2.0, -2.0)))

	It will also relocate values to enforce the high-low expectation:

	>>> t.box(((-4,0),(-2,-3)))
	postgresql.types.box(((-2.0, 0.0), (-4.0, -3.0)))

	That is:

	               (-2, 0) `high`
	                  |
	                  |
	   (-4,-3) -------+-x
	    `low`         y
	
	This happens because ``-4`` is less than ``-2``; therefore the ``-4``
	belongs on the low point. This is consistent with what PostgreSQL does
	with its ``box`` type.
	"""
	high = property(fget = lambda s: s[0])
	low = property(fget = lambda s: s[1])
	center = property(
		fget = lambda s: point((
			(s[0][0] + s[1][0]) / 2.0,
			(s[0][1] + s[1][1]) / 2.0
		))
	)

	def __new__(subtype, hl):
		if isinstance(hl, box):
			return hl
		one, two = hl
		if one[0] > two[0]:
			hx = one[0]
			lx = two[0]
		else:
			hx = two[0]
			lx = one[0]
		if one[1] > two[1]:
			hy = one[1]
			ly = two[1]
		else:
			hy = two[1]
			ly = one[1]
		return tuple.__new__(subtype, (point((hx, hy)), point((lx, ly))))

	def __repr__(self):
		return '%s.%s((%s, %s))' %(
			type(self).__module__,
			type(self).__name__,
			tuple.__repr__(self[0]),
			tuple.__repr__(self[1]),
		)

	def __str__(self):
		'Comma separate the box\'s points'
		return '%s,%s' %(self[0], self[1])

class circle(tuple):
	'circle type--center point and radius'
	center = property(fget = lambda s: s[0])
	radius = property(fget = lambda s: s[1])

	def __new__(subtype, pair):
		center, radius = pair
		if radius < 0:
			raise ValueError("radius is subzero")
		return tuple.__new__(subtype, (point(center), float(radius)))

	def __repr__(self):
		return '%s.%s((%s, %s))' %(
			type(self).__module__,
			type(self).__name__,
			tuple.__repr__(self[0]),
			repr(self[1])
		)

	def __str__(self):
		return '<%s,%s>' %(self[0], self[1])

class array(object):
	def unroll_nest(hier, dimensions):
		"return an iterator over the absolute elements of a nested sequence"
		weight = []
		elc = 1
		dims = list(dimensions[:-1])
		dims.reverse()
		for x in dims:
			weight.insert(0, elc)
			elc *= x

		for x in xrange(elc):
			v = hier
			for w in weight:
				d, r = divmod(x, w)
				v = v[d]
				x = r
			for i in v:
				yield i
	unroll_nest = staticmethod(unroll_nest)

	def detect_dimensions(hier, seqtypes = (tuple, list)):
		'Detect the dimensions of a nested sequence'
		while type(hier) in seqtypes or type(hier) is array:
			if type(hier) is array:
				for x in hier.dimensions:
					yield x
				break

			yield len(hier)
			hier = hier[0]
	detect_dimensions = staticmethod(detect_dimensions)

	def from_nest(subtype, nest, seqtypes = None, offset = None):
		'Create an array from a nested sequence'
		dims = list(subtype.detect_dimensions(
			nest, **(seqtypes and {'seqtypes': seqtypes} or {})
		))
		if offset:
			dims = dims[:len(dims)-offset]
		return subtype(tuple(subtype.unroll_nest(nest, dims)), dims)
	from_nest = classmethod(from_nest)

	def __new__(subtype, elements, dimensions = None, **kw):
		if dimensions is None:
			return subtype.from_nest(elements, **kw)
		rob = object.__new__(subtype)
		rob.elements = elements
		rob.dimensions = dimensions
		if dimensions:
			d1 = dimensions[0]
			elcount = 1
			for x in rob.dimensions:
				elcount *= x
		else:
			d1 = 0
			elcount = 0

		if len(rob.elements) != elcount:
			raise TypeError(
				"array element count inconsistent with dimensions"
			)
		rob.position = ()
		rob.slice = slice(0, d1)

		weight = []
		cw = 1
		rdim = list(dimensions)
		rdim.reverse()
		for x in rdim[:-1]:
			cw *= x
			weight.insert(0, cw)
		rob.weight = tuple(weight)

		return rob

	def arrayslice(self, subpos):
		'Create an array based on itself'
		rob = object.__new__(type(self))
		rob.elements = self.elements
		rob.dimensions = self.dimensions
		rob.position = self.position
		rob.weight = self.weight
		d = self.dimensions[len(self.position)]
		newslice = slice(
			self.slice.start + (subpos.start or 0),
			# Can't extend the slice, so grab whatever is the least.
			min((
				self.slice.start + (subpos.stop or d),
				self.slice.stop or d
			))
		)
		rob.slice = newslice
		return rob
	
	def subarray(self, idx):
		rob = object.__new__(type(self))
		rob.elements = self.elements
		rob.dimensions = self.dimensions
		rob.weight = self.weight
		idx = self.slice.start + idx
		rob.position = self.position + (slice(idx, self.slice.stop),)
		rob.slice = slice(0, rob.dimensions[len(rob.position)])
		return rob

	def nest(self, seqtype = list):
		'Transform the array into a nested sequence'
		rl = []
		for x in self:
			if type(self) is type(x):
				rl.append(x.nest())
			else:
				rl.append(x)
		return seqtype(rl)

	def __repr__(self):
		# XXX: This doesn't consider elements
		#      that might be seen as dimensions.
		return '%s.%s(%r)' %(
			type(self).__module__,
			type(self).__name__,
			self.nest()
		)

	def __len__(self):
		sl = self.slice
		return sl.stop - sl.start
	
	def __eq__(self, ob):
		return tuple(self) == ob

	def __ne__(self, ob):
		return tuple(self) != ob

	def __gt__(self, ob):
		return tuple(self) > ob

	def __lt__(self, ob):
		return tuple(self) < ob
	
	def __le__(self, ob):
		return tuple(self) <= ob

	def __ge__(self, ob):
		return tuple(self) >= ob

	def __getitem__(self, item):
		if isinstance(item, slice):
			return self.arrayslice(item)
		else:
			if item < 0:
				item = item + (self.slice.stop - self.slice.start)

			npos = len(self.position)
			ndim = len(self.dimensions)
			if npos == ndim - 1:
				# get the actual element
				idx = self.slice.start + item
				if not (0 <= idx < self.dimensions[-1]):
					return None
				for x in xrange(npos):
					pos = self.position[x]
					dim = self.dimensions[x]
					# Out of bounds position
					if not (0 <= pos.start < dim) or pos.start >= pos.stop:
						return None
					idx += pos.start * self.weight[x]

				return self.elements[idx]
			else:
				# get a new array at that level
				return self.subarray(item)

	def __iter__(self):
		for x in xrange(len(self)):
			yield self[x]

oid_to_type = {
	VARBITOID: varbit,
	BITOID: bit,

	MACADDROID: macaddr,
	CIDROID: cidr,
	INETOID: inet,

	POINTOID: point,
	BOXOID: box,
	LSEGOID: lseg,
	CIRCLEOID: circle,
}
