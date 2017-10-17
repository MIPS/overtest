# -*- encoding: utf-8 -*-
# $Id: version.py,v 1.1 2008/01/04 21:07:57 jwp Exp $
##
# copyright 2005, pg/python project.
# http://python.projects.postgresql.org
##
'PQ version class'
from types import TupleType
from struct import pack, unpack

class Version(TupleType):
	"""Version((major, minor)) -> Version

	Version serializer and parser.
	"""
	major = property(fget = lambda s: s[0])
	minor = property(fget = lambda s: s[1])

	def __new__(subtype, (major, minor)):
		major = int(major)
		minor = int(minor)
		# If it can't be packed like this, it's not a valid version.
		pack('!HH', major, minor)
		return TupleType.__new__(subtype, (major, minor))

	def __int__(self):
		return (self[0] << 16) | self[1]

	def __str__(self):
		return pack('!HH', self[0], self[1])

	def __repr__(self):
		return '%d.%d' %(self[0], self[1])

	def parse(self, data):
		return self(unpack('!HH', data))
	parse = classmethod(parse)

CancelRequestCode = Version((1234, 5678))
NegotiateSSLCode = Version((1234, 5679))
V2_0 = Version((2, 0))
V3_0 = Version((3, 0))
