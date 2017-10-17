# -*- encoding: utf-8 -*-
# $Id: test_interface.py,v 1.2 2008/01/25 03:12:31 jwp Exp $
##
# copyright 2006, pg/python project.
# http://python.projects.postgresql.org
##
import unittest

callables = (
	'query', 'execute', 'proc', 'xact'
)
containers = (
	'settings',
)

class aspects(unittest.TestCase):
	def testExistence(self):
		for x in callables + containers:
			self.failUnless(hasattr(gtx, x),
				'Connection has no attribute %s' %(x,))
	
	def testCallability(self):
		for x in callables:
			self.failUnless(callable(getattr(gtx, x)),
				'Connection attribute %s is not callable' %(x,))

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(this)
