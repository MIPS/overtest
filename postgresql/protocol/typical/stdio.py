# -*- encoding: utf-8 -*-
# $Id: stdio.py,v 1.6 2008/05/19 04:14:16 jwp Exp $
##
# copyright 2007, pg/python project.
# http://python.projects.postgresql.org
##
"""
Typical PostgreSQL type I/O routines

I/O maps for converting wire data into standard Python objects.
"""
import datetime
import postgresql.types as pg_type
import postgresql.protocol.typical.pstruct as ps

pg_epoch_datetime = datetime.datetime(2000, 1, 1)
pg_epoch_date = pg_epoch_datetime.date()
pg_date_offset = pg_epoch_date.toordinal()
## Difference between Postgres epoch and Unix epoch.
## Used to convert a Postgres ordinal to an ordinal usable by datetime
pg_time_days = (pg_date_offset - datetime.date(1970, 1, 1).toordinal())

date_io = (
	lambda x: ps.date_pack(x.toordinal() - pg_date_offset),
	lambda x: datetime.date.fromordinal(pg_date_offset + ps.date_unpack(x))
)

def timestamp_pack(x):
	"""
	Create a (seconds, microseconds) pair from a `datetime.datetime` instance.
	"""
	d = (x - pg_epoch_datetime)
	return (d.days * 24 * 60 * 60 + d.seconds, d.microseconds)

def timestamp_unpack(seconds):
	"""
	Create a `datetime.datetime` instance from a (seconds, microseconds) pair.
	"""
	return pg_epoch_datetime + datetime.timedelta(
		seconds = seconds[0], microseconds = seconds[1]
	)

def time_pack(x):
	"""
	Create a (seconds, microseconds) pair from a `datetime.time` instance.
	"""
	return (
		(x.hour * 60 * 60) + (x.minute * 60) + x.second,
		x.microsecond
	)

def time_unpack(seconds_ms):
	"""
	Create a `datetime.time` instance from a (seconds, microseconds) pair.
	Seconds being offset from epoch.
	"""
	seconds, ms = seconds_ms
	minutes, sec = divmod(seconds, 60)
	hours, min = divmod(minutes, 60)
	return datetime.time(hours, min, sec, ms)

def interval_pack(x):
	"""
	Create a (months, days, (seconds, microseconds)) tuple from a
	`datetime.timedelta` instance.
	"""
	return (
		0, x.days,
		(x.seconds, x.microseconds)
	)

def interval_unpack(mds):
	"""
	Given a (months, days, (seconds, microseconds)) tuple, create a
	`datetime.timedelta` instance.
	"""
	months, days, seconds_ms = mds
	sec, ms = seconds_ms
	return datetime.timedelta(
		days = days + (months * 30),
		seconds = sec, microseconds = ms
	)

##
# FIXME: Ignore time zone.
def timetz_pack(x):
	"""
	Create a ((seconds, microseconds), timezone) tuple from a `datetime.time`
	instance.
	"""
	return (time_pack(x), 0)

def timetz_unpack(tstz):
	"""
	Create a `datetime.time` instance from a ((seconds, microseconds), timezone)
	tuple.
	"""
	return time_unpack(tstz[0])

datetimemap = {
	pg_type.INTERVALOID : (interval_pack, interval_unpack),
	pg_type.TIMEOID : (time_pack, time_unpack),
	pg_type.TIMESTAMPOID : (time_pack, time_unpack),
}

time_io = {
	pg_type.TIMEOID : (
		lambda x: ps.time_pack(time_pack(x)),
		lambda x: time_unpack(ps.time_unpack(x))
	),
	pg_type.TIMETZOID : (
		lambda x: ps.timetz_pack(timetz_pack(x)),
		lambda x: timetz_unpack(ps.timetz_unpack(x))
	),
	pg_type.TIMESTAMPOID : (
		lambda x: ps.time_pack(timestamp_pack(x)),
		lambda x: timestamp_unpack(ps.time_unpack(x))
	),
	pg_type.TIMESTAMPTZOID : (
		lambda x: ps.time_pack(timestamp_pack(x)),
		lambda x: timestamp_unpack(ps.time_unpack(x))
	),
	pg_type.INTERVALOID : (
		lambda x: ps.interval_pack(interval_pack(x)),
		lambda x: interval_unpack(ps.interval_unpack(x))
	),
}
time_io_noday = time_io.copy()
time_io_noday[pg_type.INTERVALOID] = (
	lambda x: ps.interval_noday_pack(interval_pack(x)),
	lambda x: interval_unpack(ps.interval_noday_unpack(x))
)

time64_io = {
	pg_type.TIMEOID : (
		lambda x: ps.time64_pack(time_pack(x)),
		lambda x: time_unpack(ps.time64_unpack(x))
	),
	pg_type.TIMETZOID : (
		lambda x: ps.timetz64_pack(timetz_pack(x)),
		lambda x: timetz_unpack(ps.timetz64_unpack(x))
	),
	pg_type.TIMESTAMPOID : (
		lambda x: ps.time64_pack(timestamp_pack(x)),
		lambda x: timestamp_unpack(ps.time64_unpack(x))
	),
	pg_type.TIMESTAMPTZOID : (
		lambda x: ps.time64_pack(timestamp_pack(x)),
		lambda x: timestamp_unpack(ps.time64_unpack(x))
	),
	pg_type.INTERVALOID : (
		lambda x: ps.interval64_pack(interval_pack(x)),
		lambda x: interval_unpack(ps.interval64_unpack(x))
	),
}
time64_io_noday = time64_io.copy()
time64_io_noday[pg_type.INTERVALOID] = (
	lambda x: ps.interval64_noday_pack(interval_pack(x)),
	lambda x: interval_unpack(ps.interval64_noday_unpack(x))
)

def circle_unpack(x):
	"""
	Given raw circle data, (x, y, radius), make a circle instance using
	`postgresql.types.circle`.
	"""
	return pg_type.circle(((x[0], x[1]), x[2]))

def cidr_unpack(x):
	"""
	Given serialized cidr data, make a `postgresql.types.cidr` instance.
	"""
	fam, mask, data = ps.cidr_unpack(x)
	# cidr will determine family from len of data.
	return pg_type.cidr.from_data_mask(data, mask)

def two_pair(x):
	'Make a pair of pairs out of a sequence of four objects'
	return ((x[0], x[1]), (x[2], x[3]))

bitio = (
	lambda x: ps.varbit_pack((x.bits, x.data)),
	lambda x: pg_type.varbit.from_bits(*ps.varbit_unpack(x))
)

# Map type oids to a (pack, unpack) pair.
stdio = {
	pg_type.DATEOID : date_io,
	pg_type.VARBITOID : bitio,
	pg_type.BITOID : bitio,

	pg_type.INETOID : (
		lambda x: ps.inet_pack(x.data),
		lambda x: pg_type.inet.from_data(ps.inet_unpack(x))
	),

	pg_type.CIDROID : (
		# INET family is 2, INET6 family is 3.
		lambda x: ps.cidr_pack((len(x.data) == 4 and 2 or 3, x.mask, x.data)),
		cidr_unpack
	),

	pg_type.MACADDROID : (
		lambda x: x.data,
		lambda x: pg_type.macaddr.from_data(x)
	),

	pg_type.POINTOID : (
		ps.point_pack,
		lambda x: pg_type.point(ps.point_unpack(x))
	),

	pg_type.BOXOID : (
		lambda x: ps.box_pack((x[0][0], x[0][1], x[1][0], x[1][1])),
		lambda x: pg_type.box(two_pair(ps.box_unpack(x)))
	),

	pg_type.LSEGOID : (
		lambda x: ps.lseg_pack((x[0][0], x[0][1], x[1][0], x[1][1])),
		lambda x: pg_type.lseg(two_pair(ps.lseg_unpack(x)))
	),

	pg_type.CIRCLEOID : (
		lambda x: ps.circle_pack((x[0][0], x[0][1], x[1])),
		lambda x: circle_unpack(ps.circle_unpack(x))
	),
}
