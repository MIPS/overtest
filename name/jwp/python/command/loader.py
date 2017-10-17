# -*- encoding: utf-8 -*-
# $Id: loader.py 521 2008-05-30 00:23:55Z jwp $
##
# copyright 2007, James William Pye. http://jwp.name
##
"""
Provides a service to identify loaders for arbitrary address strings.
Given 'module:*' or 'file://', find_loader with return a loader descriptor
for using the Python code.

The directory object is a list of triples(loader descriptors):
	(LoaderTitle, LoaderClass, AddressExtractor)

The file_loader has a triple in the directory consisting of:
   ("Python file", file_loader, extract_filepath)
extract_filepath with return not-None when given a string that starts with
'file://'; when This happend, the loader search function knows that it found
a loader for the string.

The titles are useful in cases where a loader ambiguously fails by simply
returning None(pkgutil.get_loader will do this). An informative message using
the loader's title can be sent to the user in such cases.
"""
import os
import sys
try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

try:
	from pkgutil import get_loader as module_loader
except ImportError:
	try:
		from imp import get_loader as module_loader
	except ImportError:
		module_loader = None

if module_loader is None:
	try:
		from imp import find_module
	except ImportError:
		pass

	class module_loader(object):
		"""
		module loader for Pythons without pkgutil
		"""
		def __new__(self, path):
			ffp = self._getf(path)
			# keep it consistent with get_loader.
			if ffp is None:
				return
			rob = object.__new__(module_loader)
			rob._source = ffp[0].read()
			rob._path = ffp[1]
			rob._fullpath = path
			return rob

		def _getf(path):
			try:
				return find_module(path)
			except ImportError:
				pass
			# try the dots first(?), then the slashes.
			try:
				slashpath = path.replace('.', '/')
				if slashpath != path:
					return find_module(slashpath)
			except ImportError:
				try:
					##
					# Last ditch effort.
					#
					# find_module failed on us. Take the last route available
					# and import the module; it wastes cycles, and may even
					# be inappropriate, but in such cases let the user fix their
					# script.
					dsp = path.replace('/', '.')
					mod = __import__(path, None, None, path.split('.')[:-1])

					# If a loader is available, use its get_source method.
					if hasattr(mod, '__loader__'):
						src = mod.__loader__.get_source(path)
						srcio = StringIO()
						srcio.write(src)
						srcio.seek(0)
						return (srcio, path)
					else:
						try:
							return (open(mod.__file__), mod.__file__)
						except:
							pass
				except ImportError:
					# There is no module at that path.
					pass
		_getf = staticmethod(_getf)

		def get_filename(self, fullpath):
			if fullpath == self._fullpath:
				return self._path
			raise ImportError(
				"Loader for module %s cannot handle module %s" %(
					self._fullpath, fullpath
				)
			)

		def get_source(self, fullpath):
			if fullpath == self._fullpath:
				return self._source
			raise ImportError(
				"Loader for module %s cannot handle module %s" %(
					self._fullpath, fullpath
				)
			)

		def get_code(self, fullpath):
			if fullpath == self._fullpath:
				return compile(self._source, fullpath, 'exec')
			raise ImportError(
				"Loader for module %s cannot handle module %s" %(
					self._fullpath, fullpath
				)
			)

class single_loader(object):
	"""
	used for "loading" string modules(think -c)
	"""
	def __init__(self, source):
		self.source = source

	def get_filename(self, fullpath):
		if fullpath == self.source:
			return '<command>'

	def get_code(self, fullpath):
		if fullpath == self.source:
			return compile(self.source, '<command>', 'single')

	def get_source(self, fullpath):
		if fullpath == self.source:
			return self.source

class file_loader(object):
	"""
	used for "loading" scripts
	"""
	def __init__(self, filepath, fileobj = None):
		self.filepath = filepath
		if fileobj is not None:
			self._source = fileobj.read()

	def get_filename(self, fullpath):
		if fullpath == self.filepath:
			return self.filepath

	def get_source(self, fullpath):
		if fullpath == self.filepath:
			return self._read()

	def _read(self):
		if hasattr(self, '_source'):
			return self._source
		f = file(self.filepath)
		try:
			return f.read()
		finally:
			f.close()

	def get_code(self, fullpath):
		if fullpath != self.filepath:
			return
		return compile(self._read(), self.filepath, 'exec')

def extract_filepath(x):
	if x.startswith('file://'):
		return x[7:]
	return None

def extract_module(x):
	if x.startswith('module:'):
		return x[7:]
	return None

module_loader_descriptor = (
	'Python module', module_loader, extract_module
)
file_loader_descriptor = (
	'Python script', file_loader, extract_filepath
)
single_loader_descriptor = (
	'Python command', single_loader, lambda x: x
)

_directory = (
	module_loader_descriptor,
	file_loader_descriptor
)
directory = list(_directory)

def find_loader(ident, dir = directory):
	for x in dir:
		xid = x[2](ident)
		if xid is not None:
			return x
##
# vim: ts=3:sw=3:noet:
