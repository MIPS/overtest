# -*- encoding: utf-8 -*-
# $Id: test.py,v 1.2 2008/01/18 07:00:17 jwp Exp $
##
# copyright 2007, pg/python project.
# http://python.projects.postgresql.org
##
import unittest
import tempfile

def cmbx(t):
	'Yield a list of combinations using a mask'
	tl = len(t)
	return [
		[x & m and t[x-1] or '' for x in xrange(1, tl + 1)]
		for m in xrange(1, (2 ** tl) + 1)
	]

iri_samples = (
	'host/dbname/path?param=val#frag',
	'{ssh remotehost nc "$(cat%_somehost%_)" 5432}',
	'user:pass@{ssh remotehost nc somehost 5432}/dbname',
	'#frag',
	'?param=val',
	'?param=val#frag',
	'user@',
	':pass@',
	'u:p@h',
	'u:p@h:1',
)

iri_abnormal_normal_samples = {
	u'pq://fæm.com:123/õéf/á?param=val' :
		'pq://xn--fm-1ia.com:123/%x000F5%x000E9f/%x000E1?param=val',
	u'pq://l»»@fæm.com:123/õéf/á?param=val' :
		'pq://l%x000BB%x000BB@xn--fm-1ia.com:123'
		'/%x000F5%x000E9f/%x000E1?param=val',
	u'pq://fæᎱᏋm.com/õéf/á?param=val' :
		'pq://xn--fm-1ia853qzd.com/%x000F5%x000E9f/%x000E1?param=val',
}

# Split IRI bases
iri_split_samples = [
	('host:1111', 'dbname', 'path', 'param=val&param2=val', 'frag'),
	('host:1111', 'dbname', 'paths:p2', 'param=val&param2=val', 'frag'),
	('host', 'dbname', 'paths:p2', 'p2=val', 'frag()'),
# IPvN
	('[::1]:9876', 'dbname', 'paths:p2', 'p2=val', 'frag()'),
# Some unicode lovin'
	(u'fæm.com', u'dátabÁse', u'pôths:p2', u'p2=vïl', u'frag(ëì)'),
	(u'fæm.com:5432', u'dátabÁse',
		u'pôths:p2', u'p2=vïl', u'frag(ëì)'),
	('{ssh h nc localhost 5432}', 'dbname',
		'paths:p2', 'p2=val', 'frag()'),
	('{::1}:9876', 'dbname', 'paths:p2', 'p2=val', 'frag()'),
#	('%xfa.:5432', 'dátabÁse', 'pôths:p2-postfix:p3', 'p2=vïl', 'frag(ëì)'),
]

sample_structured_parameters = [
	{
		'host' : 'hostname',
		'port' : 1234,
		'database' : 'foo_db',
	},
	{
		'process' : ['ssh', 'u@foo.com', 'nc localhost 8976'],
		'database' : 'foo_db',
	},
	{
		'user' : 'username',
		'database' : 'database_name',
		'settings' : {'foo':'bar','feh':'bl%,23'},
	},
	{
		'user' : 'username',
		'database' : 'database_name',
	},
	{
		'database' : 'database_name',
	},
	{
		'user' : 'user_name',
	},
	{
		'password' : 'passwd',
	},
	{
		'host' : 'hostname',
	},
	{
		'user' : 'username',
		'password' : 'pass',
		'port' : 4321,
		'database' : 'database_name',
		'path' : ['path'],
		'fragment' : 'random_data',
	}
]

escaped_unescaped = [
	('%_', ' '),
	('%N', '\n'),
	('%T', '\t'),
	('%%', '%'),
	# Doesn't match. (invalid percent escape)
	('foo%bzr', 'foo%bzr'),
	(u'foo%bar', u'foo\xbar'),
	('foo%00bar', 'foo\0bar'),
	('foo%_bar', 'foo bar'),
	('foo%x000E6bar', u'fooæbar'),
	('foo%x000E6bar', u'fooæbar'),
	('', ''),
]

percent_values = {
	0x0 : '%00',
	0x1 : '%01',
	0x10 : '%10',
	0x20 : '%20',
	0x23 : '%23',
	0x93 : '%93',
	0xA0 : '%x000A0',
	0xFFFF : '%x0FFFF',
}

sample_split_paths = (
	['foo', 'bar'],
	[':'],
	[':', '/'],
	['colon:', '/slash'],
	['/'],
	[':/'],
	['/:'],
	['foo'],
	['foo:bar', 'feh'],
	['foo/bar'],
	['::foo/bar'],
	['p'],
	['\x00'],
	[':\x00:'],
	[':\x00:', '!@#$%^&'],
)

sample_paths = (
	'foobar',
	'%3A',
	'%2F',
	'%3A%2F',
	'%2F%3A',
	'foo',
	'foo%3Abar',
	'foo%2Fbar',
	'%3A%3Afoo%2Fbar',
	'p',
	'%00',
	'%3A%00%3A',
)

sample_netlocs = (
	'user:pass@host:1234',
	'us%3Aer:p%40ss@host:1234',
	'user@host',
	':pass@host',
	':pass@:4321',
	':pass@host:1234',
	'user:pass@host:1234',
	'{cmd}',
	'user@{cmd}',
	'user@{cmd @foo}',
	'user:pass@{cmd @foo}',
	':pass@{cmd @foo}',
	':pass@{cmd }',
)

sample_split_netlocs = (
	('user', 'pass', 'host', '1234'),
	('us@er', 'p@ss', 'host', '1234'),
	(u'îíus@:er', u'p@:ss', u'æçèêíãøú.com'.encode('idna'), '5432'),
	(u'us@:er', u'íáp@:ss', u'æçèêíãøú.com'.encode('idna'), '5432'),
)

import postgresql.utility.client.iri as client_iri
class iri(unittest.TestCase):
	def testEscapes(self):
		for e, u in escaped_unescaped:
			self.failUnless(client_iri.unescape(e) == u,
				'escape incongruity, %r(%r) != %r' %(
					e, client_iri.unescape(e), u
				)
			)

	def testPercentValue(self):
		for k, v in percent_values.iteritems():
			self.failUnless(
				v == client_iri.percent_value(k),
				'percent_value %x did not make %r, rather %r' %(
					k, v, client_iri.percent_value(k),
				)
			)
	
	def testSplitPath(self):
		for x in sample_paths:
			y = client_iri.split_path(x)
			xy = client_iri.unsplit_path(y)
			self.failUnless(
				xy == x,
				'path split-unsplit incongruity %r -> %r -> %r' %(
					x, y, xy
				)
			)

	def testUnsplitPath(self):
		for x in sample_split_paths:
			y = client_iri.unsplit_path(x)
			xy = client_iri.split_path(y)
			self.failUnless(
				xy == x,
				'path unsplit-split incongruity %r -> %r -> %r' %(
					x, y, xy
				)
			)

	def testSplitUnsplitNetloc(self):
		for x in sample_netlocs:
			y = client_iri.split_netloc(x)
			xy = client_iri.unsplit_netloc(y)
			self.failUnless(
				xy == x,
				'netloc split-unsplit incongruity %r -> %r -> %r' %(
					x, y, xy
				)
			)

	def testUnsplitSplitNetloc(self):
		for t in sample_split_netlocs:
			for x in cmbx(t):
				x = tuple(x)
				y = client_iri.unsplit_netloc(x)
				xy = client_iri.split_netloc(y)
				self.failUnless(
					xy == x,
					'netloc unsplit-split incongruity %r -> %r -> %r' %(
						x, y, xy
					)
				)

	def testSplitUnsplit(self):
		scheme = 'pq://'
		for x in iri_samples:
			xs = client_iri.split(x)
			uxs = client_iri.unsplit(xs)
			self.failUnless(
				x.strip('/ ') == uxs[len(scheme):].rstrip('/ '),
				"split-unsplit incongruity, %r -> %r -> %r" %(
					x, xs, uxs
				)
			)

	def testUnsplitSplit(self):
		for scheme in ('pq', 'pqs',):
			for b in iri_split_samples:
				for x in cmbx(b):
					x.insert(0, scheme)
					x = tuple(x)
					xs = client_iri.unsplit(x)
					uxs = client_iri.split(xs)
					self.failUnless(
						uxs == x,
						"unsplit-split incongruity, %r -> %r -> %r" %(
							x, xs, uxs
						)
					)

	def testParseSerialize(self):
		scheme = 'pq://'
		for x in iri_samples:
			xs = client_iri.parse(x)
			uxs = client_iri.serialize(xs)
			c1 = client_iri.unescape(x.strip('/ '))
			c2 = client_iri.unescape(uxs[len(scheme):].strip('/ '))
			self.failUnless(
				c1 == c2,
				"parse-serialize incongruity, %r -> %r -> %r : %r != %r" %(
					x, xs, uxs, c1, c2
				)
			)
	
	def testSerializeParse(self):
		for x in sample_structured_parameters:
			xs = client_iri.serialize(x)
			uxs = client_iri.parse(xs)
			self.failUnless(
				x == uxs,
				"serialize-parse incongruity, %r -> %r -> %r" %(
					x, xs, uxs,
				)
			)

	def testConstructStructure(self):
		for x in sample_structured_parameters:
			y = client_iri.construct(x)
			xy = client_iri.structure(y)
			self.failUnless(
				x == xy,
				"construct-structre incongruity, %r -> %r -> %r" %(
					x, y, xy
				)
			)

	def testConstructStructure(self):
		for x in sample_structured_parameters:
			y = client_iri.construct(x)
			xy = client_iri.structure(y)
			self.failUnless(
				x == xy,
				"construct-structre incongruity, %r -> %r -> %r" %(
					x, y, xy
				)
			)

	def testNormalize(self):
		for abn, norm in iri_abnormal_normal_samples.iteritems():
			normalized = client_iri.normalize(abn)
			self.failUnless(
				normalized == norm,
				"normalization failure, {%r: %r} != %r" %(
					abn, norm, normalized
				)
			)

import postgresql.utility.client.option as client_option
class option(unittest.TestCase):
	def testOptions(self):
		import optparse
		optparser = optparse.OptionParser(
			"%prog", version = "0",
			add_help_option = False
		)
		optparser.add_options(client_option.default)
		args = {
			'-d' : 'my_dbname',
			'-p' : '5432',
			'-U' : 'my_username',
			'--server-options' : 'my_options',
		}
		l = []
		for x, y in args.iteritems():
			l.append(x)
			l.append(y)
		co, ca = optparser.parse_args(l)
		for x in args:
			for y in client_option.default:
				if x.startswith('--'):
					if x in y._long_opts:
						break
				else:
					if x in y._short_opts:
						break
			self.failUnless(
				args[x] == str(getattr(co, y.dest)),
				"parsed argument %r did not map to value %r, rather %r" %(
					x, args[x], getattr(co, y.dest)
				)
			)

from StringIO import StringIO

passfile_sample = """
host:1111:dbname:user:password1
*:1111:dbname:user:password2
*:*:dbname:user:password3
*:*:*:user:password4
*:*:*:usern:password4.5
*:*:*:*:password5
"""

passfile_sample_map = {
	('user', 'host', '1111', 'dbname') : 'password1',
	('user', 'host', '1111', 'dbname') : 'password1',
	('user', 'foo', '1111', 'dbname') : 'password2',
	('user', 'foo', '4321', 'dbname') : 'password3',
	('user', 'foo', '4321', 'db,name') : 'password4',

	('uuser', 'foo', '4321', 'db,name') : 'password5',
	('usern', 'foo', '4321', 'db,name') : 'password4.5',
	('foo', 'bar', '19231', 'somedbn') : 'password5',
}

difficult_passfile_sample = r"""
host\\:1111:db\:name:u\\ser:word1
*:1111:\:dbname\::\\user\\:pass\:word2
foohost:1111:\:dbname\::\\user\\:pass\:word3
"""

difficult_passfile_sample_map = {
	('u\\ser','host\\','1111','db:name') : 'word1',
	('\\user\\','somehost','1111',':dbname:') : 'pass:word2',
	('\\user\\','someotherhost','1111',':dbname:') : 'pass:word2',
	# More specific, but comes after '*'
	('\\user\\','foohost','1111',':dbname:') : 'pass:word2',
	('','','','') : None,
}


import postgresql.utility.client.pgpass as client_pgpass
class pgpass(unittest.TestCase):
	def runTest(self):
		sample1 = client_pgpass.parse(StringIO(passfile_sample))
		sample2 = client_pgpass.parse(StringIO(difficult_passfile_sample))

		for k, pw in passfile_sample_map.iteritems():
			lpw = client_pgpass.lookup_password(sample1, k)
			self.failUnless(lpw == pw,
				"password lookup incongruity, expecting %r got %r with %r"
				" in \n%s" %(
					pw, lpw, k, passfile_sample
				)
			)

		for k, pw in difficult_passfile_sample_map.iteritems():
			lpw = client_pgpass.lookup_password(sample2, k)
			self.failUnless(lpw == pw,
				"password lookup incongruity, expecting %r got %r with %r"
				" in \n%s" %(
					pw, lpw, k, difficult_passfile_sample
				)
			)

service_file = tempfile.mktemp()
sf = open(service_file, 'w')
try:
	sf.write("""
[foo]
user=foo_user
host=foo.com
""")
finally:
	sf.close()

env_samples = [
	(
		{
			'PGUSER' : 'the_user',
			'PGHOST' : 'the_host',
		},
		{
			'user' : 'the_user',
			'host' : 'the_host',
		}
	),
	(
		{
			'PGIRI' : 'pqs://localhost:5432/dbname/ns'
		},
		{
			'sslmode' : 'require',
			'host' : 'localhost',
			'port' : 5432,
			'database' : 'dbname',
			'path' : ['ns']
		}
	),
	(
		{
			'PGIRI' : 'pq://localhost:5432/dbname/ns',
			'PGHOST' : 'override',
		},
		{
			'host' : 'override',
			'port' : 5432,
			'database' : 'dbname',
			'path' : ['ns']
		}
	),
	(
		{
			'PGUNIX' : '/path',
			'PGROLE' : 'myrole',
		},
		{
			'unix' : '/path',
			'role' : 'myrole'
		}
	),
	(
		{
			'PGSERVICEFILE' : service_file,
			'PGSERVICE' : 'foo',
			'PGHOST' : 'unseen',
			'PGPORT' : 5432,
		},
		{
			'user' : 'foo_user',
			'host' : 'foo.com',
			'port' : 5432,
		}
	)
]

import postgresql.utility.client.environ as client_environ
class environ(unittest.TestCase):
	def runTest(self):
		for env, dst in env_samples:
			z = client_environ.convert_environ(env)
			self.failUnless(dst == z,
				"environment conversion incongruity %r -> %r != %r" %(
					env, z, dst
				)
			)

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(this)
