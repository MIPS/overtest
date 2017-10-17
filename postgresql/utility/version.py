# -*- encoding: utf-8 -*-
# $Id: version.py,v 1.4 2008/05/20 03:07:19 jwp Exp $
##
# copyright 2005, pg/python project.
# http://python.projects.postgresql.org
##
"""
PostgreSQL version parsing.

>>> postgresql.utility.version.split('8.0.1')
(8, 0, 1, None, None)

>>> postgresql.utility.version.compare(
...  postgresql.utility.split('8.0.1'),
...  postgresql.utility.split('8.0.1'),
... )
0
"""

def split(vstr):
	"""
	Split a PostgreSQL version string into a tuple
	(major,minor,patch,state_class,state_level)
	"""
	v = vstr.strip().split('.', 3)

	# Get rid of the numbers around the state_class (beta,a,dev,alpha)
	state_class = v[-1].strip('0123456789')
	if state_class:
		last_version_num, state_level = v[-1].split(state_class)
		if not state_level:
			state_level = None
		else:
			state_level = int(state_level)
	else:
		last_version_num = v[-1]
		state_level = None
		state_class = None

	if last_version_num:
		last_version_num = int(last_version_num)
	else:
		last_version_num = None
	
	if len(v) == 3:
		major = int(v[0])
		if v[1]:
			minor = int(v[1])
		else:
			minor = None
		patch = last_version_num
	elif len(v) == 2:
		major = int(v[0])
		minor = last_version_num
		patch = None
	else:
		major = last_version_num
		minor = None
		patch = None

	return (
		major,
		minor,
		patch,
		state_class,
		state_level
	)

def unsplit(vtup):
	'join a version tuple back into a version string'
	return '%s%s%s%s%s' %(
		vtup[0],
		vtup[1] is not None and '.' + str(vtup[1]) or '',
		vtup[2] is not None and '.' + str(vtup[2]) or '',
		vtup[3] is not None and str(vtup[3]) or '',
		vtup[4] is not None and str(vtup[4]) or ''
	)

default_state_class_priority = [
	'dev',
	'a',
	'alpha',
	'b',
	'beta',
	'rc',
	None,
]

def compare(
	v1, v2,
	state_class_priority = default_state_class_priority,
	cmp = cmp
):
	"""
	Compare the given versions using the given `cmp` function after translating
	the state class of each version into a numeric value derived by the class's
	position in the given `state_class_priority`.

	`cmp` and `state_class_priority` have default values.
	"""
	v1l = list(v1)
	v2l = list(v2)
	try:
		v1l[-2] = state_class_priority.index(v1[-2])
	except ValueError:
		raise ValueError("first argument has unknown state class %r" %(v1[-2],))
	try:
		v2l[-2] = state_class_priority.index(v2[-2])
	except ValueError:
		raise ValueError("second argument has unknown state class %r" %(v2[-2],))
	return cmp(v1l, v2l)

class one(tuple):
	'First generation PostgreSQL version structure'
	formats = ('xml', 'sh',)
	map = {
		'major':0,
		'minor':1,
		'patch':2,
		'state':3,
		'level':4,
	}

	def __new__(subtype, major, minor, patch = None, state = '', level = 0):
		return tuple.__new__(subtype, (
			int(major or 0),
			int(minor or 0),
			int(patch or 0),
			str(state or ''),
			int(level or 0)
		))

	def parse(cls, string):
		return cls(*split(string))
	parse = classmethod(parse)

	def __repr__(self):
		return '%s.%s(%s)' %(
			type(self).__module__,
			type(self).__name__,
			tuple.__repr__(self)
		)

	def __getitem__(self, i):
		if i in one.map:
			i = one.map[i]
		return tuple.__getitem__(self, i)

	def __getattr__(self, a):
		if a in one.map:
			return tuple.__getitem__(self, one.map[a])
		return tuple.__getattr__(self, a)

	def __setattr__(self, a, v):
		raise AttributeError('attribute "%s" is immutable' %(a,))

	def __str__(self):
		if self.level > 0 and self.state != '':
			l = str(self.level)
		else:
			l = ''
		if self.patch > 0:
			p = '.' + str(self.patch)
		else:
			p = ''
		return '%d.%d%s%s%s' %(self.major, self.minor, p, self.state, l)

	def cmp_version(self, vsplit):
		"""
		Compare Postgres versions generally 8.0.4 == 8.0 == 8
		This function expects a version.one object or a version.split tuple.
		"""
		for x in xrange(5):
			if vsplit[x] is None:
				continue
			if vsplit[x] != self[x]:
				return False
		return True

	def cmp_version_str(self, xstr):
		return self.cmp_version(split(xstr))

	def python(self):
		return repr(self)

	def xml(self):
		return '<version type="one">\n' + \
			' <major>' + str(self.major) + '</major>\n' + \
			' <minor>' + str(self.minor) + '</minor>\n' + \
			' <patch>' + str(self.patch) + '</patch>\n' + \
			' <state>' + str(self.state) + '</state>\n' + \
			' <level>' + str(self.level) + '</level>\n' + \
			'</version>'

	def sh(self):
		return """PG_VERSION_MAJOR=%s
PG_VERSION_MINOR=%s
PG_VERSION_PATCH=%s
PG_VERSION_STATE=%s
PG_VERSION_LEVEL=%s""" %(
	str(self.major),
	str(self.minor),
	str(self.patch),
	str(self.state),
	str(self.level),
)

def parse(vstr):
	"Create a 'one' version object(default) from the given version string"
	return one.parse(vstr)

if __name__ == '__main__':
	import sys
	from optparse import OptionParser
	op = OptionParser()
	op.add_option('-f', '--format',
		type='choice',
		dest='format',
		help='format of output information',
		choices=('sh', 'xml', 'python'),
		default='sh',
	)
	op.add_option('-t', '--type',
		type='choice',
		dest='type',
		help='type of version string to parse',
		choices=('auto', 'one',),
		default='auto',
	)
	op.set_usage(op.get_usage().strip() + ' "version to parse"')
	co, ca = op.parse_args()
	if len(ca) != 1:
		op.error('requires exactly one argument, the version')
	if co.type != 'auto':
		v = getattr(sys.modules[__name__], co.type).parse(ca[0])
	else:
		v = parse(ca[0])
	sys.stdout.write(getattr(v, co.format)())
	sys.stdout.write('\n')
