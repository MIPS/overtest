# -*- encoding: utf-8 -*-
# $Id: test_strings.py,v 1.2 2008/02/03 17:09:36 jwp Exp $
##
# copyright 2008, pg/python project.
# http://python.projects.postgresql.org
##
import sys
import os
import unittest
import postgresql.strings as pg_str

# strange possibility, split, normalized
split_qname_samples = [
	('base', ['base'], 'base'),
	('bASe', ['base'], 'base'),
	('"base"', ['base'], 'base'),
	('"base "', ['base '], '"base "'),
	('" base"', [' base'], '" base"'),
	('" base"""', [' base"'], '" base"""'),
	('""" base"""', ['" base"'], '""" base"""'),
	('".base"', ['.base'], '".base"'),
	('".base."', ['.base.'], '".base."'),
	('schema.base', ['schema', 'base'], 'schema.base'),
	('"schema".base', ['schema', 'base'], 'schema.base'),
	('schema."base"', ['schema', 'base'], 'schema.base'),
	('"schema.base"', ['schema.base'], '"schema.base"'),
	(u'schEmÅ."base"', [u'schemå', 'base'], u'schemå.base'),
	('scheMa."base"', ['schema', 'base'], 'schema.base'),
	('" schema"."base"', [' schema', 'base'], '" schema".base'),
	('" schema"."ba se"', [' schema', 'ba se'], '" schema"."ba se"'),
	('" ""schema"."ba""se"', [' "schema', 'ba"se'], '" ""schema"."ba""se"'),
	('" schema" . "ba se"', [' schema', 'ba se'], '" schema"."ba se"'),
	(' " schema" . "ba se"	', [' schema', 'ba se'], '" schema"."ba se"'),
	(' ". schema." . "ba se"	', ['. schema.', 'ba se'], '". schema."."ba se"'),
	('CAT . ". schema." . "ba se"	', ['cat', '. schema.', 'ba se'],
		'cat.". schema."."ba se"'),
	('"cat" . ". schema." . "ba se"	', ['cat', '. schema.', 'ba se'],
		'cat.". schema."."ba se"'),
	('"""cat" . ". schema." . "ba se"	', ['"cat', '. schema.', 'ba se'],
		'"""cat".". schema."."ba se"'),
	('"""cÅt" . ". schema." . "ba se"	', ['"cÅt', '. schema.', 'ba se'],
		'"""cÅt".". schema."."ba se"'),
]

split_samples = [
	('', ['']),
	('one-to-one', ['one-to-one']),
	('"one-to-one"', [
		'',
		('"', 'one-to-one'),
		''
	]),
	('$$one-to-one$$', [
		'',
		('$$', 'one-to-one'),
		''
	]),
	("E'one-to-one'", [
		'',
		("E'", 'one-to-one'),
		''
	]),
	("E'on''e-to-one'", [
		'',
		("E'", "on''e-to-one"),
		''
	]),
	("E'on''e-to-\\'one'", [
		'',
		("E'", "on''e-to-\\'one"),
		''
	]),
	("'one\\'-to-one'", [
		'',
		("'", "one\\'-to-one"),
		''
	]),

	('"foo"""', [
		'',
		('"', 'foo""'),
		'',
	]),

	('"""foo"', [
		'',
		('"', '""foo'),
		'',
	]),

	("'''foo'", [
		'',
		("'", "''foo"),
		'',
	]),
	("'foo'''", [
		'',
		("'", "foo''"),
		'',
	]),
	("E'foo\\''", [
		'',
		("E'", "foo\\'"),
		'',
	]),
	(r"E'foo\\' '", [
		'',
		("E'", r"foo\\"),
		' ',
		("'", ''),
	]),
	(r"E'foo\\'' '", [
		'',
		("E'", r"foo\\'' "),
		'',
	]),

	('select \'foo\' as "one"', [
		'select ',
		("'", 'foo'),
		' as ',
		('"', 'one'),
		''
	]),
	('select $$foo$$ as "one"', [
		'select ',
		("$$", 'foo'),
		' as ',
		('"', 'one'),
		''
	]),
	('select $b$foo$b$ as "one"', [
		'select ',
		("$b$", 'foo'),
		' as ',
		('"', 'one'),
		''
	]),
	('select $b$', [
		'select ',
		('$b$', ''),
	]),

	('select $1', [
		'select $1',
	]),

	('select $1$', [
		'select $1$',
	]),
]

split_sql_samples = [
	('select 1; select 1', [
		['select 1'],
		[' select 1']
	]),
	('select \'one\' as "text"; select 1', [
		['select ', ("'", 'one'), ' as ', ('"', 'text'), ''],
		[' select 1']
	]),
	('select \'one\' as "text"; select 1', [
		['select ', ("'", 'one'), ' as ', ('"', 'text'), ''],
		[' select 1']
	]),
	('select \'one;\' as ";text;"; select 1; foo', [
		['select ', ("'", 'one;'), ' as ', ('"', ';text;'), ''],
		(' select 1',),
		[' foo'],
	]),
	('select \'one;\' as ";text;"; select $$;$$; foo', [
		['select ', ("'", 'one;'), ' as ', ('"', ';text;'), ''],
		[' select ', ('$$', ';'), ''],
		[' foo'],
	]),
	('select \'one;\' as ";text;"; select $$;$$; foo;\';b\'\'ar\'', [
		['select ', ("'", 'one;'), ' as ', ('"', ';text;'), ''],
		[' select ', ('$$', ';'), ''],
		(' foo',),
		['', ("'", ";b''ar"), ''],
	]),
]

class test_strings(unittest.TestCase):
	def test_split(self):
		for unsplit, split in split_samples:
			xsplit = list(pg_str.split(unsplit))
			self.failUnlessEqual(xsplit, split)
			self.failUnlessEqual(pg_str.unsplit(xsplit), unsplit)
	
	def test_split_sql(self):
		for unsplit, split in split_sql_samples:
			xsplit = list(pg_str.split_sql(unsplit))
			self.failUnlessEqual(xsplit, split)
			self.failUnlessEqual(';'.join([pg_str.unsplit(x) for x in xsplit]), unsplit)

	def test_qname(self):
		"indirectly tests split_using"
		for unsplit, split, norm in split_qname_samples:
			xsplit = pg_str.split_qname(unsplit)
			self.failUnlessEqual(xsplit, split)
			self.failUnlessEqual(pg_str.qname(*split), norm)

		self.failUnlessRaises(
			ValueError,
			pg_str.split_qname, '"foo'
		)
		self.failUnlessRaises(
			ValueError,
			pg_str.split_qname, 'foo"'
		)
		self.failUnlessRaises(
			ValueError,
			pg_str.split_qname, 'bar.foo"'
		)
		self.failUnlessRaises(
			ValueError,
			pg_str.split_qname, 'bar".foo"'
		)

	def test_quotes(self):
		self.failUnlessEqual(
			pg_str.quote_literal_strict("""foo'bar"""),
			"""'foo''bar'"""
		)
		self.failUnlessEqual(
			pg_str.quote_literal("""foo'bar"""),
			"""E'foo''bar'"""
		)
		self.failUnlessEqual(
			pg_str.quote_literal("""\\foo'bar\\"""),
			"""E'\\\\foo''bar\\\\'"""
		)
		self.failUnlessEqual(
			pg_str.quote_literal_strict("""\\foo'bar\\"""),
			"""'\\foo''bar\\'"""
		)
		self.failUnlessEqual(
			pg_str.quote_ident('''\\foo'bar\\'''),
			'''"\\foo'bar\\"'''
		)
		self.failUnlessEqual(
			pg_str.escape_ident('"'),
			'""',
		)
		self.failUnlessEqual(
			pg_str.escape_ident('""'),
			'""""',
		)
		chars = ''.join([
			unichr(x) for x in xrange(10000)
			if unichr(x) != '"'
		])
		self.failUnlessEqual(
			pg_str.escape_ident(chars),
			chars,
		)
		chars = ''.join([
			unichr(x) for x in xrange(10000)
			if unichr(x) != "'"
		])
		self.failUnlessEqual(
			pg_str.escape_literal_strict(chars),
			chars,
		)
		chars = ''.join([
			unichr(x) for x in xrange(10000)
			if unichr(x) not in "\\'"
		])
		self.failUnlessEqual(
			pg_str.escape_literal(chars),
			chars,
		)

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(this)
