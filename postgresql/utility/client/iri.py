# -*- encoding: utf-8 -*-
# $Id: iri.py,v 1.5 2008/05/20 02:17:38 jwp Exp $
##
# copyright 2007, pg/python project.
# http://python.projects.postgresql.org
##
"""
Split, parse, serialize, and structure PQ IRIs.

PQ IRIs take the form::

	pq://user:pass@host:port/database/public:schema3?setting=value#fragment

They are IRIs as unicode escapes will be converted to their corresponding
character where necessary. Colons are used to separate schemas names for the
search_path, and connection settings are specified using IRI arguments. The
fragment portion of the IRI is used to title the connection; something that can
be used to help trace operations or exceptions on a given connection.

Liking to ``https``, the sslmode can be set to "require" by::

	pqs://user:pass@host:port/database/public:schema2?setting=value

IPv6 is supported via the standard representation::

	pq://[::1]:5432/database

Some shorthands for common escapes are also supported. The following illustrates
an alternative way to represent spaces::

	pq://host/db%_with%_spaces

Other special percent escapes::

	%% -> '%'
	%_ -> ' '
	%N -> '\\n'
	%T -> '\\t'
	%S -> '/'

In addition to host based addressing, process based addressing is supported as
well using curly braces::

	pq://{ssh 'nc localhost 5432'}/dbname
"""

import re
import shlex

# So what if they're non-standard. ;)
# The escaping functions only use the hex escapes.
percent_map = {
	'%%' : '%',
	'%_' : ' ',
	'%N' : '\n',
	'%T' : '\t',
	'%S' : '/',
}
unescaped = ''.join([']'] + [chr(x) for x in xrange(33, 127) if x != ord(']')])
del x
unescape_re = re.compile(
	'(?:' + '|'.join(percent_map.iterkeys()) + ')|' + \
	'(?:%(?<=[^%]%)|^%)(?:x([0-9a-fA-F]{5,5})|([0-9a-fA-F]{2,2}))'
)
escape_re = re.compile('[^%s]' %(unescaped,))

def unescape_sub(exc, m):
	'resolve percent escapes for an re.sub() call'
	if m.group(0) in percent_map:
		val = ord(percent_map[m.group(0)])
	else:
		val = int(m.group(1) or m.group(2), 16)
	if val in exc:
		return m.group(0)
	return unichr(val)

def unescape(x, exc = ()):
	'Substitute percent escapes with literal characters'
	return unescape_re.sub(lambda m: unescape_sub(exc, m), x)

def percent_value(x):
	'Return the appropriate percent escape for the given value'
	if x >= 0xA0:
		return '%%x%0.5X' %(x,)
	return '%%%0.2X' %(x,)

def escape(x, extra = ''):
	'Substitute literal characters with percent escapes'
	if extra:
		return re.sub('[^%s]|[%s]' %(unescaped, re.escape(extra)),
			lambda m: percent_value(ord(m.group(0))), x)
	return escape_re.sub(lambda m: percent_value(ord(m.group(0))), x)

indexes = {
	'scheme' : 0,
	'netloc' : 1,
	'database' : 2,
	'paths' : 3,
	'query' : 4,
	'fragment' : 5
}

def split(s, defaultscheme = 'pq'):
	"""
	Split a Postgres IRI into its base components.
	Return a 6-tuple: (scheme, netloc, database, schema_paths, rtparams, fragment)
	"""
	pos = 0
	next_pos = 0
	scheme = ''
	if s.startswith('pq://'):
		scheme = 'pq'
	elif s.startswith('pqs://'):
		scheme = 'pqs'
	if scheme:
		pos = len(scheme) + 3
	else:
		scheme = defaultscheme

	# Find the end of the netloc
	next_pos = s.find('/', pos)
	if next_pos == -1:
		# Just a scheme and a location.
		return (scheme, s[pos:], '', '', '', '')
	brace = s.find('{', pos)
	if brace != -1 and brace < next_pos:
		# Command reference?
		next_pos = s.find('}', brace)
		if next_pos == -1:
			raise ValueError('unclosed command reference started at %d' %(brace,))
		next_pos = s.find('/', next_pos)
		if next_pos == -1:
			# Just a scheme and a command reference with a / in it.
			return (scheme, s[pos:], '', '', '', '')

	netloc = s[pos:next_pos]
	pos = next_pos + 1

	# Find the end of the database name
	next_pos = min(filter(
		lambda x: x != -1,
		(s.find('/', pos), s.find('?', pos), s.find('#', pos),)
	) or (-1,))
	if next_pos == -1:
		return (scheme, netloc, s[pos:], '', '', '')
	else:
		database = s[pos:next_pos]
		pos = next_pos + 1

	# Find the end of the paths
	if s[next_pos] == '/':
		next_pos = min(filter(
			lambda x: x != -1,
			(s.find('?', pos), s.find('#', pos),)
		) or (-1,))
		if next_pos == -1:
			return (scheme, netloc, database, s[pos:], '', '')
		else:
			paths = s[pos:next_pos]
			pos = next_pos + 1
	else:
		paths = ''

	# Find the end of the query [rtparams]
	if s[next_pos] == '?':
		next_pos = s.find('#', pos)
		if next_pos == -1:
			return (scheme, netloc, database, paths, s[pos:], '')
		else:
			# Every component was indicated
			return (
				scheme, netloc, database,
				paths, s[pos:next_pos], s[next_pos+1:]
			)
	else:
		# No query, just a fragment.
		return (scheme, netloc, database, paths, '', s[next_pos+1:])

def split_path(p):
	'return a list of unescaped strings split on ":"'
	return [unescape(x) for x in p.split(':')]

def unsplit_path(p):
	'join a list of paths(strings) on ":" after escaping them'
	return ':'.join([escape(x, ':/') for x in p])

def unsplit(t):
	'Make a PQ IRI from a PQ tuple of connection elements'
	post_slash = '%s%s%s%s' %(
		t[2],
		(t[3] and ('/' + t[3]) or ''),
		(t[4] and ('?' + t[4]) or ''),
		(t[5] and ('#' + t[5]) or ''),
	)
	return "%s://%s%s%s" % (
		t[0], t[1], post_slash and '/', post_slash,
	)

def unsplit_normalized(t):
	'Unsplit and normalize for storage or transmission'
	last = u"%s%s%s%s" %(
		t[2],
		(t[3] and ('/' + t[3]) or ''),
		(t[4] and ('?' + t[4]) or ''),
		(t[5] and ('#' + t[5]) or ''),
	)
	return "%s://%s/%s" % (
		t[0], unsplit_netloc(split_netloc(t[1])), escape(last)
	)

def split_netloc(netloc):
	'Split a net location into a 4-tuple, (user, password, host, port)'
	passwd = ''
	user = ''
	pos = netloc.find('@')
	brace = netloc.find('{')
	if pos == -1:
		# No user information
		pos = 0
	elif pos < brace or brace == -1:
		up = netloc[:pos].split(':', 1)
		user = up[0]
		if len(up) == 2:
			passwd = up[1]
		pos = pos + 1
	else:
		pos = 0

	user = unescape(user)
	passwd = unescape(passwd)
	if pos >= len(netloc):
		return (user, passwd, '', '')

	pos_chr = netloc[pos]
	if pos_chr == '{':
		# Process pipe
		next_pos = netloc.find('}', pos)
		if next_pos == -1:
			raise ValueError, 'unclosed command reference started at %d' %(
				pos,
			)
		addr = netloc[pos:next_pos+1]
		port = ''
	elif pos_chr == '[':
		# IPvN addr
		next_pos = netloc.find(']', pos)
		if next_pos == -1:
			raise ValueError, "unclosed IPv6 address block: %r" %(
				netloc[pos:],
			)
		addr = netloc[pos:next_pos+1]
		pos = next_pos + 1
		next_pos = netloc.find(':', pos)
		if next_pos == -1:
			port = ''
		else:
			port = netloc[next_pos+1:]
	else:
		next_pos = netloc.find(':', pos)
		if next_pos == -1:
			addr = netloc[pos:]
			port = ''
		else:
			addr = netloc[pos:next_pos]
			port = netloc[next_pos+1:]

	return (user, passwd, addr, port)

def unsplit_netloc(t):
	'Create a netloc IRI fragment from the given tuple(user,password,host,port)'
	return '%s%s%s%s%s%s%s' %(
		# User can be unconditionally included
		escape(t[0], '][@:/?#'),
		# If a password, include the ':'
		t[1] and ':' or '', escape(t[1], '][@/?#'),
		# If user or password, include the '@'
		(t[0] or t[1]) and '@' or '',
		# Unconditionally include host
		t[2].startswith('{') and t[2] or t[2].encode('idna'),
		# If port, include the ':'
		t[3] and ':', t[3]
	)

def structure(t):
	'Create a dictionary of connection parameters from a six-tuple'
	d = {}

	if t[0] == 'pqs':
		d['sslmode'] = 'require'

	uphp = split_netloc(t[1])
	if uphp[0]:
		d['user'] = uphp[0]
	if uphp[1]:
		d['password'] = uphp[1]
	if uphp[2].startswith('{'):
		d['process'] = [
			unescape(x) for x in uphp[2].strip('{}').split(' ')
		]
	else:
		if uphp[2]:
			d['host'] = uphp[2]
		if uphp[3]:
			d['port'] = int(uphp[3])

	if t[2]:
		d['database'] = t[2]

	# Path support
	if t[3]:
		d['path'] = split_path(t[3])

	if t[4]:
		d['settings'] = dict([
			[unescape(y) for y in x.split('=', 1)]
			for x in t[4].split('&')
		])

	if t[5]:
		d['fragment'] = t[5]
	return d

def construct(x):
	'Construct a IRI tuple from a dictionary object'
	return (
		bool(x.get('ssl')) is False and 'pq' or 'pqs',
		# netloc: user:pass@{host[:port]|process}
		unsplit_netloc((
			x.get('user', ''),
			x.get('password', ''),
			x.get('process', None) is not None and '{%s}' %(
				' '.join([escape(y) for y in x['process']])
			) or x.get('host', ''),
			x.get('port', '')
		)),
		escape(x.get('database', '') or '', '/'),
		# Path
		unsplit_path(x.get('path', [])),
		x.get('settings', None) is not None and '&'.join([
			'%s=%s' %(k, v.replace('&','%26'))
			for k, v in x['settings'].iteritems()
		]),
		'fragment' in x and x['fragment'] or ''
	)

def parse(s):
	'Parse a Postgres IRI into a dictionary object'
	return structure(split(s))

def serialize(x):
	'Return a Postgres IRI from a dictionary object.'
	return unsplit(construct(x))

def normalize(y):
	'Take an un-normalized IRI and escape the invalid characters'
	return unsplit_normalized(split(y))
