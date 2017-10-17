# -*- encoding: utf-8 -*-
# $Id: test.py,v 1.2 2008/05/15 14:36:58 jwp Exp $
##
# copyright 2008, pg/python project.
# http://python.projects.postgresql.org
##
import unittest
import struct
import postgresql.protocol.pqueue.element3 as e3
import postgresql.protocol.pqueue.client3 as c3
import postgresql.protocol.pqueue.pbuffer as p_buffer_module
try:
	import postgresql.protocol.pqueue.cbuffer as c_buffer_module
except ImportError:
	c_buffer_module = None

class buffer_test(object):
	def setUp(self):
		self.buffer = self.bufferclass()

	def testMultiByteMessage(self):
		b = self.buffer
		b.write('s')
		self.failUnless(b.next_message() is None)
		b.write('\x00\x00')
		self.failUnless(b.next_message() is None)
		b.write('\x00\x10')
		self.failUnless(b.next_message() is None)
		data = 'twelve_chars'
		b.write(data)
		self.failUnless(b.next_message() == ('s', data))

	def testSingleByteMessage(self):
		b = self.buffer
		b.write('s')
		self.failUnless(b.next_message() is None)
		b.write('\x00')
		self.failUnless(b.next_message() is None)
		b.write('\x00\x00\x05')
		self.failUnless(b.next_message() is None)
		b.write('b')
		self.failUnless(b.next_message() == ('s', 'b'))

	def testEmptyMessage(self):
		b = self.buffer
		b.write('x')
		self.failUnless(b.next_message() is None)
		b.write('\x00\x00\x00')
		self.failUnless(b.next_message() is None)
		b.write('\x04')
		self.failUnless(b.next_message() == ('x', ''))

	def testInvalidLength(self):
		b = self.buffer
		b.write('y\x00\x00\x00\x03')
		self.failUnlessRaises(ValueError, b.next_message,)

	def testRemainder(self):
		b = self.buffer
		b.write('r\x00\x00\x00\x05Aremainder')
		self.failUnless(b.next_message() == ('r', 'A'))

	def testLarge(self):
		b = self.buffer
		factor = 1024
		range = 10000
		b.write('X' + struct.pack("!L", factor * range + 4))
		segment = '\0' * factor
		for x in xrange(range-1):
			b.write(segment)
		b.write(segment)
		msg = b.next_message()
		self.failUnless(msg is not None)
		self.failUnless(msg[0] == 'X')

if c_buffer_module is not None:
	class c_buffer(buffer_test, unittest.TestCase):
		bufferclass = c_buffer_module.pq_message_stream

class p_buffer(buffer_test, unittest.TestCase):
	bufferclass = p_buffer_module.pq_message_stream

message_samples = [
	e3.VoidMessage,
	e3.Startup(
		user = 'jwp',
		database = 'template1',
		options = '-f',
	),
	e3.Notice(
		severity = 'FATAL',
		message = 'a descriptive message',
		code = 'FIVEC',
		detail = 'bleh',
		hint = 'dont spit into the fan',
	),
	e3.Notify(123, "wood_table"),
	e3.KillInformation(19320, 589483),
	e3.ShowOption('foo', 'bar'),
	e3.Authentication(4, 'salt'),
	e3.Complete('SELECT'),
	e3.Ready('I'),
	e3.CancelQuery(4123, 14252),
	e3.NegotiateSSL(),
	e3.Password('ckr4t'),
	e3.AttributeTypes(()),
	e3.AttributeTypes(
		(123,) * 1
	),
	e3.AttributeTypes(
		(123,0) * 1
	),
	e3.AttributeTypes(
		(123,0) * 2
	),
	e3.AttributeTypes(
		(123,0) * 4
	),
	e3.TupleDescriptor(()),
	e3.TupleDescriptor((
		('name', 123, 1, 1, 0, 0, 1,),
	)),
	e3.TupleDescriptor((
		('name', 123, 1, 2, 0, 0, 1,),
	) * 2),
	e3.TupleDescriptor((
		('name', 123, 1, 2, 1, 0, 1,),
	) * 3),
	e3.TupleDescriptor((
		('name', 123, 1, 1, 0, 0, 1,),
	) * 1000),
	e3.Tuple([]),
	e3.Tuple(['foo',]),
	e3.Tuple([None]),
	e3.Tuple(['foo','bar']),
	e3.Tuple([None, None]),
	e3.Tuple([None, 'foo', None]),
	e3.Tuple(['bar', None, 'foo', None, 'bleh']),
	e3.Tuple(['foo','bar'] * 100),
	e3.Tuple([None] * 100),
	e3.Query('select * from u'),
	e3.Parse('statement_id', 'query', (123, 0)),
	e3.Parse('statement_id', 'query', (123,)),
	e3.Parse('statement_id', 'query', ()),
	e3.Bind('portal_id', 'statement_id',
		[('tt','data'),('\x00\x00',None)], ('ff','xx')),
	e3.Bind('portal_id', 'statement_id',
		[('tt',None)], ('xx',)),
	e3.Bind('portal_id', 'statement_id', [('ff','data')], ()),
	e3.Bind('portal_id', 'statement_id', [], ('xx',)),
	e3.Bind('portal_id', 'statement_id', [], ()),
	e3.Execute('portal_id', 500),
	e3.Execute('portal_id', 0),
	e3.DescribeStatement('statement_id'),
	e3.DescribePortal('portal_id'),
	e3.CloseStatement('statement_id'),
	e3.ClosePortal('portal_id'),
	e3.Function(123, [], 'xx'),
	e3.Function(321, [('tt', 'foo'),], 'xx'),
	e3.Function(321, [('tt', None),], 'xx'),
	e3.Function(321, [('aa', None),('aa', 'a' * 200)], 'xx'),
	e3.FunctionResult(''),
	e3.FunctionResult('foobar'),
	e3.FunctionResult(None),
	e3.CopyToBegin(123, [321,123]),
	e3.CopyToBegin(0, [10,]),
	e3.CopyToBegin(123, []),
	e3.CopyFromBegin(123, [321,123]),
	e3.CopyFromBegin(0, [10]),
	e3.CopyFromBegin(123, []),
	e3.CopyData(''),
	e3.CopyData('foo'),
	e3.CopyData('a' * 2048),
	e3.CopyFail(''),
	e3.CopyFail('iiieeeeee!'),
]

class test_element3(unittest.TestCase):
	def testParseSerializeConsistency(self):
		for msg in message_samples:
			smsg = msg.serialize()
			self.failUnlessEqual(
				msg, msg.parse(smsg),
			)

	def testEmptyMessages(self):
		for x in e3.__dict__.itervalues():
			if isinstance(x, e3.EmptyMessage):
				xtype = type(x)
				self.failUnless(x is xtype())

xact_samples = [
	# Simple contrived exchange.
	(
		(
			e3.Query("COMPLETE"),
		), (
			e3.Complete('COMPLETE'),
			e3.Ready('I'),
		)
	),
	(
		(
			e3.Query("ROW DATA"),
		), (
			e3.TupleDescriptor((
				('foo', 1, 1, 1, 1, 1, 1),
				('bar', 1, 2, 1, 1, 1, 1),
			)),
			e3.Tuple(('lame', 'lame')),
			e3.Complete('COMPLETE'),
			e3.Ready('I'),
		)
	),
	(
		(
			e3.Query("ROW DATA"),
		), (
			e3.TupleDescriptor((
				('foo', 1, 1, 1, 1, 1, 1),
				('bar', 1, 2, 1, 1, 1, 1),
			)),
			e3.Tuple(('lame', 'lame')),
			e3.Tuple(('lame', 'lame')),
			e3.Tuple(('lame', 'lame')),
			e3.Tuple(('lame', 'lame')),
			e3.Ready('I'),
		)
	),
	(
		(
			e3.Query("NULL"),
		), (
			e3.Null(),
			e3.Ready('I'),
		)
	),
	(
		(
			e3.Query("COPY TO"),
		), (
			e3.CopyToBegin(1, [1,2]),
			e3.CopyData('row1'),
			e3.CopyData('row2'),
			e3.CopyDone(),
			e3.Complete('COPY TO'),
			e3.Ready('I'),
		)
	),
	(
		(
			e3.Function(1, [('', '')], 1),
		), (
			e3.FunctionResult('foo'),
			e3.Ready('I'),
		)
	),
	(
		(
			e3.Parse("NAME", "SQL", ()),
		), (
			e3.ParseComplete(),
		)
	),
	(
		(
			e3.Bind("NAME", "STATEMENT_ID", (), ()),
		), (
			e3.BindComplete(),
		)
	),
	(
		(
			e3.Parse("NAME", "SQL", ()),
			e3.Bind("NAME", "STATEMENT_ID", (), ()),
		), (
			e3.ParseComplete(),
			e3.BindComplete(),
		)
	),
	(
		(
			e3.Describe("STATEMENT_ID"),
		), (
			e3.AttributeTypes(()),
			e3.NoData(),
		)
	),
	(
		(
			e3.Describe("STATEMENT_ID"),
		), (
			e3.AttributeTypes(()),
			e3.TupleDescriptor(()),
		)
	),
	(
		(
			e3.CloseStatement("foo"),
		), (
			e3.CloseComplete(),
		),
	),
	(
		(
			e3.ClosePortal("foo"),
		), (
			e3.CloseComplete(),
		),
	),
	(
		(
			e3.Synchronize(),
		), (
			e3.Ready('I'),
		),
	),
]

class test_client3(unittest.TestCase):
	def testTransactionSamplesAll(self):
		for xcmd, xres in xact_samples:
			x = c3.Transaction(xcmd)
			r = tuple([(y.type, y.serialize()) for y in xres])
			x.state[1]()
			self.failUnlessEqual(x.messages, ())
			x.state[1](r)
			self.failUnlessEqual(x.state[0], c3.Complete)
			rec = []
			for y in x.completed:
				for z in y[1]:
					if type(z) is type(''):
						z = e3.CopyData(z)
					rec.append(z)
			self.failUnlessEqual(xres, tuple(rec))

	def testReprocessing(self):
		pass

	def testError(self):
		pass

	def testFatalError(self):
		pass

	def testLastReady(self):
		pass

	def testAsynchronous(self):
		pass

	def testCopyTo(self):
		pass

	def testCopyFrom(self):
		pass

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(this)
