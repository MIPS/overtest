# -*- encoding: utf-8 -*-
# $Id: element3.py,v 1.1.4.1 2008/06/22 11:08:29 jwp Exp $
##
# copyright 2005, pg/python project.
# http://python.projects.postgresql.org
##
'PQ version 3.0 elements'
import sys, os
from types import TupleType, StringType, ObjectType, DictionaryType
import struct
from struct import pack, unpack

if hasattr(struct, 'Struct'):
	L_struct = struct.Struct("!L")
	UNLONG = lambda x: L_struct.unpack(x)[0]
	H_struct = struct.Struct("!H")
	SHORT = H_struct.pack
	UNSHORT = lambda x: H_struct.unpack(x)[0]
else:
	def UNLONG(s): return unpack("!L", s)[0]
	def SHORT(i): return pack("!H", i)
	def UNSHORT(s): return unpack("!H", s)[0]
BYTE = chr
UNBYTE = ord

StringFormat = intern('\x00\x00')
BinaryFormat = intern('\x00\x01')

class ParseError(Exception): pass

class Message(ObjectType):
	__slots__ = ()
	def __repr__(self):
		return '%s.%s(%s)' %(
			type(self).__module__,
			type(self).__name__,
			', '.join(repr(getattr(self, x)) for x in self.__slots__)
		)

	def __eq__(self, ob):
		return isinstance(ob, type(self)) and self.type == ob.type and \
		not False in [
			getattr(self, x) == getattr(ob, x, None)
			for x in self.__slots__
		]

	def __str__(self):
		data = self.serialize()
		return self.type + pack("!L", len(data) + 4) + data

	def serialization(self, writer):
		writer(self.serialize())

	def parse(self, data):
		return self(data)
	parse = classmethod(parse)

class Void(Message):
	"""
	An absolutely empty message. When serialized, it always yields an empty
	string.
	"""
	type = ''
	__slots__ = ()

	def __str__(self):
		return ''

	def serialize(self):
		return ''
	
	def __new__(self, *args, **kw):
		return VoidMessage
VoidMessage = Message.__new__(Void)

def str_message_repr(self):
	return '%s.%s(%s)' %(
		type(self).__module__,
		type(self).__name__,
		StringType.__repr__(self),
	)

def tuple_message_repr(self):
	return '%s.%s(%s)' %(
		type(self).__module__,
		type(self).__name__,
		TupleType.__repr__(self)
	)

def dict_message_repr(self):
	return '%s.%s(**%s)' %(
		type(self).__module__,
		type(self).__name__,
		DictionaryType.__repr__(self)
	)

class WireMessage(Message, TupleType):
	type = property(fget = lambda s: s[0])
	data = property(fget = lambda s: s[1])
	__slots__ = ()

	def __new__(subtype, (type, data)):
		type = str(type)[0]
		return TupleType.__new__(subtype, (type, str(data)))
	__repr__ = tuple_message_repr

	def serialize(self):
		return self[1]

	def parse(self, data):
		if unpack("!L", data[1:5])[0] != len(data) - 1:
			raise ParseError(
				"invalid wire message where data is %d bytes and " \
				"internal size stamp is %d bytes" %(
					len(data), unpack("!L", data[1:5])[0] + 1
				)
			)
		return self((data[0], data[5:]))
	parse = classmethod(parse)

class EmptyMessage(Message):
	'An abstract message that is always empty'
	__slots__ = ()
	type = ''

	def serialize(self):
		return ''

	def parse(self, data):
		if data != '':
			raise ParseError("empty message(%r) had data" %(self.type,))
		return self()
	parse = classmethod(parse)

class Notify(Message):
	'Asynchronous notification message'
	type = 'A'
	__slots__ = ('pid', 'relation', 'parameter')

	def __init__(self, pid, relation, parameter = ''):
		self.pid = pid
		self.relation = relation
		self.parameter = parameter

	def serialize(self):
		return pack("!L", self.pid) + \
			self.relation + '\x00' + \
			self.parameter + '\x00'

	def parse(self, data):
		pid = UNLONG(data[0:4])
		relname, param, nothing = data[4:].split('\x00', 2)
		return self(pid, relname, param)
	parse = classmethod(parse)

class ShowOption(Message):
	"""ShowOption(name, value)
	GUC variable information from backend"""
	type = 'S'
	__slots__ = ('name', 'value')

	def __init__(self, name, value):
		self.name = name
		self.value = value

	def serialize(self):
		return self.name + '\x00' + self.value + '\x00'

	def parse(self, data):
		return self(*(data.split('\x00', 2)[0:2]))
	parse = classmethod(parse)

class Complete(Message, StringType):
	'Complete command'
	type = 'C'
	__slots__ = ()
	__repr__ = str_message_repr

	def serialize(self):
		return self + '\x00'

	def parse(self, data):
		return self(data[:-1])
	parse = classmethod(parse)

class Null(EmptyMessage):
	'Null command'
	type = 'I'
	__slots__ = ()
	def __new__(subtype):
		return NullMessage
NullMessage = EmptyMessage.__new__(Null)

class NoData(EmptyMessage):
	'Null command'
	type = 'n'
	__slots__ = ()
	def __new__(subtype):
		return NoDataMessage
NoDataMessage = EmptyMessage.__new__(NoData)

class ParseComplete(EmptyMessage):
	'Parse reaction'
	type = '1'
	__slots__ = ()
	def __new__(subtype):
		return ParseCompleteMessage
ParseCompleteMessage = EmptyMessage.__new__(ParseComplete)

class BindComplete(EmptyMessage):
	'Bind reaction'
	type = '2'
	__slots__ = ()
	def __new__(subtype):
		return BindCompleteMessage
BindCompleteMessage = EmptyMessage.__new__(BindComplete)

class CloseComplete(EmptyMessage):
	'Close statement or Portal'
	type = '3'
	__slots__ = ()
	def __new__(subtype):
		return CloseCompleteMessage
CloseCompleteMessage = EmptyMessage.__new__(CloseComplete)

class Suspension(EmptyMessage):
	'Portal was suspended, more tuples for reading'
	type = 's'
	__slots__ = ()
	def __new__(subtype):
		return SuspensionMessage
SuspensionMessage = EmptyMessage.__new__(Suspension)

class Ready(Message):
	'Ready for new query'
	type = intern('Z')
	__slots__ = ('xact_state',)

	def __init__(self, data):
		self.xact_state = data

	def serialize(self):
		return self.xact_state

class Notice(Message, DictionaryType):
	"""Notification message"""
	type = 'N'
	_dtm = {
		'S' : 'severity',
		'C' : 'code',
		'M' : 'message',
		'D' : 'detail',
		'H' : 'hint',
		'W' : 'context',
		'P' : 'position',
		'p' : 'internal_position',
		'q' : 'internal_query',
		'F' : 'file',
		'L' : 'line',
		'R' : 'function',
	}
	__slots__ = ()

	def __init__(self,
		severity = None,
		message = None,
		code = None,
		detail = None,
		hint = None,
		position = None,
		internal_position = None,
		internal_query = None,
		context = None,
		file = None,
		line = None,
		function = None
	):
		l = locals()
		d = self
		for v in self._dtm.itervalues():
			if v in l and l[v] is not None:
				d[v] = l[v]
	__repr__ = dict_message_repr

	def serialize(self):
		return ''.join([
			k + self[v] + '\x00'
			for k, v in self._dtm.iteritems()
			if self.get(v) is not None
		]) + '\x00'

	def parse(self, data):
		kw = {}
		for frag in data.split('\x00'):
			if frag:
				kw[self._dtm[frag[0]]] = frag[1:]
		return self(**kw)
	parse = classmethod(parse)

class Error(Notice):
	"""Incoming error"""
	type = 'E'
	__slots__ = ()

class FunctionResult(Message):
	"""Function result value"""
	type = 'V'
	__slots__ = ('result',)

	def __init__(self, datum):
		self.result = datum

	def serialize(self):
		return self.result is None and '\xff\xff\xff\xff' or \
			pack("!L", len(self.result)) + self.result
	
	def parse(self, data):
		if data == '\xff\xff\xff\xff':
			return self(None)
		size = UNLONG(data[0:4])
		data = data[4:]
		if size != len(data):
			raise ParseError(
				"data length(%d) is not equal to the specified message size(%d)" %(
					len(data), size
				)
			)
		return self(data)
	parse = classmethod(parse)

class AttributeTypes(Message, TupleType):
	"""Tuple attribute types"""
	type = 't'
	__slots__ = ()
	__repr__ = tuple_message_repr

	def serialize(self):
		return SHORT(len(self)) + ''.join([pack("!L", x) for x in self])

	def parse(self, data):
		ac = UNSHORT(data[0:2])
		args = data[2:]
		if len(args) != ac * 4:
			raise ParseError("invalid argument type data size")
		return self(unpack('!%dL'%(ac,), args))
	parse = classmethod(parse)

class TupleDescriptor(Message, TupleType):
	"""Tuple description"""
	type = intern('T')
	__slots__ = ()
	__repr__ = tuple_message_repr

	def serialize(self):
		return SHORT(len(self)) + ''.join([
			x[0] + '\x00' + pack("!LhLhlh", *x[1:])
			for x in self
		])

	def parse(self, data):
		ac = UNSHORT(data[0:2])
		atts = []
		data = data[2:]
		ca = 0
		while ca < ac:
			eoan = data.index('\0')
			name = data[0:eoan]
			data = data[eoan+1:]
			# name, relationId, columnNumber, typeId, typlen, typmod, format
			atts.append((name,) + unpack("!LhLhlh", data[0:18]))
			data = data[18:]
			ca += 1
		return self(atts)
	parse = classmethod(parse)

class Tuple(Message, TupleType):
	"""Incoming tuple"""
	type = intern('D')
	__slots__ = ()
	__repr__ = tuple_message_repr

	def serialize(self):
		return SHORT(len(self)) + ''.join([
			x is None and '\xff\xff\xff\xff' or pack("!L", len(x)) + str(x)
			for x in self
		])

	def parse(self, data):
		natts = UNSHORT(data[0:2])
		atts = list()
		offset = 2

		while natts > 0:
			alo = offset
			offset += 4
			size = data[alo:offset]
			if size == '\xff\xff\xff\xff':
				att = None
			else:
				al = UNLONG(size)
				ao = offset
				offset = ao + al
				att = data[ao:offset]
			atts.append(att)
			natts -= 1
		return self(atts)
	parse = classmethod(parse)

class KillInformation(Message):
	'Backend cancellation information'
	type = 'K'
	__slots__ = ('pid', 'key')

	def __init__(self, pid, key):
		self.pid = pid
		self.key = key

	def serialize(self):
		return pack("!LL", self.pid, self.key)

	def parse(self, data):
		return self(*unpack("!LL", data))
	parse = classmethod(parse)

class CancelQuery(KillInformation):
	'Abort the query in the specified backend'
	type = ''
	from version import CancelRequestCode as version
	__slots__ = ('pid', 'key')

	def serialize(self):
		return pack("!HHLL",
			self.version[0], self.version[1],
			self.pid, self.key
		)

	def parse(self, data):
		if data[0:4] != str(self.version):
			raise ParseError("invalid cancel query code")
		return self(*unpack("!xxxxLL", data))
	parse = classmethod(parse)

class NegotiateSSL(Message):
	"Discover backend's SSL support"
	type = ''
	from postgresql.protocol.pqueue.version import NegotiateSSLCode as version
	packed_version = pack("!HH", version[0], version[1])
	__slots__ = ()

	def __new__(subtype):
		return NegotiateSSLMessage

	def serialize(self):
		return NegotiateSSL.packed_version

	def parse(self, data):
		if data != str(self.version):
			raise ParseError("invalid SSL Negotiation code")
		return NegotiateSSLMessage
	parse = classmethod(parse)
NegotiateSSLMessage = Message.__new__(NegotiateSSL)

class Startup(Message, DictionaryType):
	'Initiate a connection'
	type = ''
	from postgresql.protocol.pqueue.version import V3_0 as version
	__slots__ = ()
	__repr__ = dict_message_repr

	def serialize(self):
		return str(self.version) + ''.join([
			k + '\x00' + v + '\x00'
			for k, v in self.iteritems() if v is not None
		]) + '\x00'

	def parse(self, data):
		if data[0:4] != str(self.version):
			raise ParseError("invalid version code")
		kw = dict()
		key = None
		for value in data[4:].split('\x00')[:-2]:
			if key is None:
				key = value
				continue
			kw[key] = value
			key = None
		return self(kw)
	parse = classmethod(parse)

AuthRequest_OK = 0
AuthRequest_KRB4 = 1
AuthRequest_KRB5 = 2
AuthRequest_Cleartext = 3
AuthRequest_Password = AuthRequest_Cleartext
AuthRequest_Crypt = 4
AuthRequest_MD5 = 5
AuthRequest_SCMC = 6
AuthRequest_GSS = 7
AuthRequest_SSPI = 9
AuthRequest_GSSContinue = 8

AuthNameMap = {
	AuthRequest_KRB4 : 'Kerberos4',
	AuthRequest_KRB5 : 'Kerberos5',
	AuthRequest_Password : 'Cleartext',
	AuthRequest_Crypt : 'Crypt',
	AuthRequest_MD5 : 'MD5',
	AuthRequest_SCMC : 'SCM Credential',
	AuthRequest_GSS : 'GSS',
	AuthRequest_SSPI : 'SSPI',
	AuthRequest_GSSContinue : 'GSSContinue',
}

class Authentication(Message):
	"""Authentication(request, salt)"""
	type = 'R'
	__slots__ = ('request', 'salt')

	def __init__(self, request, salt):
		self.request = request
		self.salt = salt

	def serialize(self):
		return pack("!L", self.request) + self.salt

	def parse(subtype, data):
		return subtype(UNLONG(data[0:4]), data[4:])
	parse = classmethod(parse)

class Password(Message, StringType):
	'Password supplement'
	type = 'p'
	__slots__ = ()
	__repr__ = str_message_repr

	def serialize(self):
		return self

class Disconnect(EmptyMessage):
	'Close the connection'
	type = 'X'
	__slots__ = ()
	def __new__(subtype):
		return DisconnectMessage
DisconnectMessage = EmptyMessage.__new__(Disconnect)

class Flush(EmptyMessage):
	'Flush'
	type = 'H'
	__slots__ = ()
	def __new__(subtype):
		return FlushMessage
FlushMessage = EmptyMessage.__new__(Flush)

class Synchronize(EmptyMessage):
	'Synchronize'
	type = 'S'
	__slots__ = ()
	def __new__(subtype):
		return SynchronizeMessage
SynchronizeMessage = EmptyMessage.__new__(Synchronize)

class Query(Message, StringType):
	"""Execute the query with the given arguments"""
	type = 'Q'
	__slots__ = ()
	__repr__ = str_message_repr

	def serialize(self):
		return self + '\x00'

	def parse(self, data):
		return self(data[0:-1])
	parse = classmethod(parse)

class Parse(Message):
	"""Parse a query with the specified argument types"""
	type = 'P'
	__slots__ = ('name', 'statement', 'argtypes')

	def __init__(self, name, statement, argtypes):
		self.name = name
		self.statement = statement
		self.argtypes = argtypes

	def parse(self, data):
		name, statement, args = data.split('\x00', 2)
		ac = UNSHORT(args[0:2])
		args = args[2:]
		if len(args) != ac * 4:
			raise ParseError("invalid argument type data")
		at = unpack('!%dL'%(ac,), args)
		return self(name, statement, at)
	parse = classmethod(parse)

	def serialize(self):
		ac = SHORT(len(self.argtypes))
		return self.name + '\x00' + self.statement + '\x00' + ac + ''.join([
			pack("!L", x) for x in self.argtypes
		])

class Bind(Message):
	"""Bind a parsed statement with the given arguments to a Portal"""
	type = 'B'
	__slots__ = ('name', 'statement', 'arguments', 'rformats')

	def __init__(self, portal, statement, args, rformats):
		self.name = portal
		self.statement = statement
		self.arguments = args
		self.rformats = rformats
	
	def serialize(self):
		args = self.arguments
		ac = SHORT(len(args))
		pf = ''.join([x[0] for x in args])
		ad = ''.join([
			(x[1] is not None and
				(pack("!L", len(x[1])) + x[1]) or
				'\xff\xff\xff\xff'
			) for x in args
		])
		rfc = SHORT(len(self.rformats))
		rfs = ''.join([rf for rf in self.rformats])
		return \
			self.name + '\x00' + self.statement + '\x00' + \
			ac + pf + ac + ad + rfc + rfs

	def parse(subtype, message_data):
		name, statement, data = message_data.split('\x00', 2)
		ac = UNSHORT(data[:2])
		offset = 2 + (2 * ac)
		argformats = unpack(("2s" * ac), data[2:offset])

		natts = UNSHORT(data[offset:offset+2])
		args = list()
		offset += 2

		while natts > 0:
			alo = offset
			offset += 4
			size = data[alo:offset]
			if size == '\xff\xff\xff\xff':
				att = None
			else:
				al = UNLONG(size)
				ao = offset
				offset = ao + al
				att = data[ao:offset]
			args.append(att)
			natts -= 1

		rfc = UNSHORT(data[offset:offset+2])
		ao = offset + 2
		offset = ao + (2 * rfc)
		rformats = unpack(("2s" * rfc), data[ao:offset])

		return subtype(name, statement, zip(argformats, args), rformats)
	parse = classmethod(parse)

class Execute(Message):
	"""Fetch results from the specified Portal"""
	type = 'E'
	__slots__ = ('name', 'max')

	def __init__(self, name, max = 0):
		self.name = name
		self.max = max

	def serialize(self):
		return self.name + '\x00' + pack("!L", self.max)
	
	def parse(self, data):
		name, max = data.split('\x00', 1)
		return self(name, UNLONG(max))
	parse = classmethod(parse)

class Describe(Message, StringType):
	"""Describe a Portal or Prepared Statement"""
	type = 'D'
	__slots__ = ()
	__repr__ = str_message_repr

	def serialize(self):
		return self.subtype + self + '\x00'

	def parse(subtype, data):
		if data[0] != subtype.subtype:
			raise ParseError(
				"invalid Describe message subtype, %r; expected %r" %(
					subtype.subtype, data[0]
				)
			)
		return subtype(data[1:-1])
	parse = classmethod(parse)

class DescribeStatement(Describe):
	subtype = 'S'
	__slots__ = ()

class DescribePortal(Describe):
	subtype = 'P'
	__slots__ = ()

class Close(Message, StringType):
	"""Generic Close"""
	type = 'C'
	__slots__ = ()
	__repr__ = str_message_repr

	def serialize(self):
		return self.subtype + self + '\x00'

	def parse(subtype, data):
		if data[0] != subtype.subtype:
			raise ParseError(
				"invalid Close message subtype, %r; expected %r" %(
					subtype.subtype, data[0]
				)
			)
		return subtype(data[1:-1])
	parse = classmethod(parse)

class CloseStatement(Close):
	"""Close the specified Statement"""
	subtype = 'S'
	__slots__ = ()

class ClosePortal(Close):
	"""Close the specified Portal"""
	subtype = 'P'
	__slots__ = ()

class Function(Message):
	"""Execute the specified function with the given arguments"""
	type = 'F'
	__slots__ = ('oid', 'arguments', 'rformat')

	def __init__(self, oid, args, rformat = StringFormat):
		self.oid = oid
		self.arguments = args
		self.rformat = rformat

	def serialize(self):
		ac = SHORT(len(self.arguments))
		return pack("!L", self.oid) + ac + ''.join([
				x[0] for x in self.arguments
			]) + ac + ''.join([
			(x[1] is None) and '\xff\xff\xff\xff' or pack("!L", len(x[1])) + x[1]
			for x in self.arguments
		]) + self.rformat

	def parse(self, data):
		oid = UNLONG(data[0:4])

		ac = UNSHORT(data[4:6])
		offset = 6 + (2 * ac)
		argformats = unpack(("2s" * ac), data[6:offset])

		natts = UNSHORT(data[offset:offset+2])
		args = list()
		offset += 2

		while natts > 0:
			alo = offset
			offset += 4
			size = data[alo:offset]
			if size == '\xff\xff\xff\xff':
				att = None
			else:
				al = UNLONG(size)
				ao = offset
				offset = ao + al
				att = data[ao:offset]
			args.append(att)
			natts -= 1

		return self(oid, zip(argformats, args), data[offset:])
	parse = classmethod(parse)

class CopyBegin(Message):
	type = None
	__slots__ = ('format', 'formats')

	def __init__(self, format, formats):
		self.format = format
		self.formats = formats

	def serialize(self):
		return chr(self.format) + SHORT(len(self.formats)) + ''.join([
			SHORT(x) for x in self.formats
		])

	def parse(subtype, data):
		format = ord(data[0])
		natts = UNSHORT(data[1:3])
		formats_str = data[3:]
		if len(formats_str) != natts * 2:
			raise ParseError("number of formats and data do not match up")
		return subtype(format, [
			UNSHORT(formats_str[x:x+2]) for x in xrange(0, natts * 2, 2)
		])
	parse = classmethod(parse)

class CopyToBegin(CopyBegin):
	"""Begin copying to"""
	type = 'H'
	__slots__ = ('format', 'formats')

class CopyFromBegin(CopyBegin):
	"""Begin copying from"""
	type = 'G'
	__slots__ = ('format', 'formats')

class CopyData(Message):
	type = intern('d')
	__slots__ = ('data',)

	def __init__(self, data):
		self.data = str(data)

	def serialize(self):
		return self.data

	def parse(subtype, data):
		return subtype(data)
	parse = classmethod(parse)

class CopyFail(Message, StringType):
	type = 'f'
	__slots__ = ()
	__repr__ = str_message_repr

	def serialize(self):
		return self + '\x00'

	def parse(self, data):
		return self(data[:-1])
	parse = classmethod(parse)

class CopyDone(EmptyMessage):
	type = 'c'
	__slots__ = ()
	def __new__(subtype):
		return CopyDoneMessage
CopyDoneMessage = EmptyMessage.__new__(CopyDone)
