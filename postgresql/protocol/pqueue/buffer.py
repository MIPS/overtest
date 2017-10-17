# -*- encoding: utf-8 -*-
# $Id: buffer.py,v 1.2 2008/05/15 18:45:49 jwp Exp $
##
# copyright 2007, pg/python project.
# http://python.projects.postgresql.org
##
"""
This is an abstraction module that provides the working buffer implementation.
If a C compiler is not available on the system that built the package, the slower
`postgresql.protocol.pqueue.pbuffer` module can be used in
`postgresql.protocol.pqueue.cbuffer`'s absence.

This provides a convenient place to import the necessary module without
concerning the local code with the details.
"""
try:
	from postgresql.protocol.pqueue.cbuffer import *
except ImportError:
	from postgresql.protocol.pqueue.pbuffer import *
