# -*- encoding: utf-8 -*-
# $Id: test_foundation.py,v 1.3 2008/01/29 05:32:44 jwp Exp $
##
# copyright 2008, pg/python project.
# http://python.projects.postgresql.org
##
import sys
import os
import unittest

from postgresql.utility.client.test import *
from postgresql.test.test_strings import *
from postgresql.encodings.test import *

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(this)
