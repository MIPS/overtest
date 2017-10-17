# -*- encoding: utf-8 -*-
# $Id: oidmaps.py,v 1.2 2008/04/01 03:00:30 jwp Exp $
##
# copyright 2007, pg/python project.
# http://python.projects.postgresql.org
##
"""
Map PostgreSQL type Oids to routines that pack and unpack raw data.

 stdio:
  The primary map.
"""
from postgresql.protocol.typical.pstruct import *
import postgresql.types as pg_type

literal = (lambda x: x, lambda x: x)

stdio = {
	pg_type.RECORDOID : (record_pack, record_unpack),
	pg_type.ANYARRAYOID : (array_pack, array_unpack),

	pg_type.BOOLOID : (bool_pack, bool_unpack),
	pg_type.BITOID : (bit_pack, bit_unpack),
	pg_type.VARBITOID : (varbit_pack, varbit_unpack),

	pg_type.BYTEAOID : (str, str),
	pg_type.CHAROID : literal,
	pg_type.MACADDROID : literal,

	pg_type.INETOID : (inet_pack, inet_unpack),
	pg_type.CIDROID : (cidr_pack, cidr_unpack),

	pg_type.DATEOID : (date_pack, date_unpack),
	pg_type.ABSTIMEOID : (long_pack, long_unpack),

	pg_type.INT2OID : (int2_pack, int2_unpack),
	pg_type.INT4OID : (int4_pack, int4_unpack),
	pg_type.INT8OID : (int8_pack, int8_unpack),

	pg_type.OIDOID : (oid_pack, oid_unpack),
	pg_type.XIDOID : (xid_pack, xid_unpack),
	pg_type.CIDOID : (cid_pack, cid_unpack),
	pg_type.TIDOID : (tid_pack, tid_unpack),

	pg_type.FLOAT4OID : (float_pack, float_unpack),
	pg_type.FLOAT8OID : (double_pack, double_unpack),

	pg_type.POINTOID : (point_pack, point_unpack),
	pg_type.LSEGOID : (lseg_pack, lseg_unpack),
	pg_type.BOXOID : (box_pack, box_unpack),
	pg_type.CIRCLEOID : (circle_pack, circle_unpack),
	pg_type.PATHOID : (path_pack, path_unpack),
	pg_type.POLYGONOID : (polygon_pack, polygon_unpack),

	#pg_type.ACLITEMOID : (aclitem_pack, aclitem_unpack),
	#pg_type.LINEOID : (line_pack, line_unpack),
	#pg_type.NUMERICOID : (numeric_pack, numeric_unpack),
	#pg_type.CASHOID : (cash_pack, cash_unpack),
}

time_io = {
	pg_type.TIMEOID : (time_pack, time_unpack),
	pg_type.TIMETZOID : (timetz_pack, timetz_unpack),
	pg_type.TIMESTAMPOID : (time_pack, time_unpack),
	pg_type.TIMESTAMPTZOID : (time_pack, time_unpack),
	pg_type.INTERVALOID : (interval_pack, interval_unpack)
}

time_noday_io = {
	pg_type.TIMEOID : (time_pack, time_unpack),
	pg_type.TIMETZOID : (timetz_pack, timetz_unpack),
	pg_type.TIMESTAMPOID : (time_pack, time_unpack),
	pg_type.TIMESTAMPTZOID : (time_pack, time_unpack),
	pg_type.INTERVALOID : (interval_noday_pack, interval_noday_unpack)
}

time64_io = {
	pg_type.TIMEOID : (time64_pack, time64_unpack),
	pg_type.TIMETZOID : (timetz64_pack, timetz64_unpack),
	pg_type.TIMESTAMPOID : (time64_pack, time64_unpack),
	pg_type.TIMESTAMPTZOID : (time64_pack, time64_unpack),
	pg_type.INTERVALOID : (interval64_pack, interval64_unpack)
}

time64_noday_io = {
	pg_type.TIMEOID : (time64_pack, time64_unpack),
	pg_type.TIMETZOID : (timetz64_pack, timetz64_unpack),
	pg_type.TIMESTAMPOID : (time64_pack, time64_unpack),
	pg_type.TIMESTAMPTZOID : (time64_pack, time64_unpack),
	pg_type.INTERVALOID : (interval64_noday_pack, interval64_noday_unpack)
}
