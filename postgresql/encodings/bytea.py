# -*- encoding: utf-8 -*-
# $Id: bytea.py,v 1.4 2007/12/14 05:20:59 jwp Exp $
##
# copyright 2007, pg/python project.
# http://python.projects.postgresql.org
##
'PostgreSQL bytea encoding registration'
import codecs

try:
	from postgresql.encodings.cbytea import *
except ImportError:
	from postgresql.encodings.pbytea import *

bytea_codec = (Codec.encode, Codec.decode, StreamReader, StreamWriter)
codecs.register(lambda x: x == 'bytea' and bytea_codec or None)
