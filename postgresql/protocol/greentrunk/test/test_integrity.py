# -*- encoding: utf-8 -*-
# $Id: test_integrity.py,v 1.5 2008/04/01 03:33:43 jwp Exp $
##
# copyright 2006, pg/python project.
# http://python.projects.postgresql.org
##
import os
import unittest
import random
import itertools

iot = '_dst'
if __name__ == '__main__':
	execute("CREATE TEMP TABLE _dst (i bigint)")
	copyin = query("COPY _dst FROM STDIN")
	loadin = query("INSERT INTO _dst VALUES ($1)")

getq = "SELECT i FROM generate_series(0, %d) AS g(i)"
copy = "COPY (%s) TO STDOUT"

def random_read(curs, remaining_rows):
	"""
	Read from one of the three methods using a random amount if sized.
	- 50% chance of curs.read(random())
	- 40% chance of next()
	- 10% chance of read() # no count
	"""
	if random.random() > 0.5:
		rrows = random.randrange(0, remaining_rows)
		return curs.read(rrows), rrows
	elif random.random() < 0.1:
		return curs.read(), -1
	else:
		try:
			return [curs.next()], 1
		except StopIteration:
			return [], 1

def random_select_get(limit):
	return query(getq %(limit - 1,))

def random_copy_get(limit):
	return query(copy %(getq %(limit - 1,),))

class test_integrity(unittest.TestCase):
	"""
	test the integrity of the get and put interfaces on queries
	and result handles.
	"""
	def test_select(self):
		total = 0
		while total < 10000:
			limit = random.randrange(500000)
			read = 0
			total += limit
			p = random_select_get(limit)()
			last = ([(-1,)], 1)
			completed = [last[0]]
			while True:
				next = random_read(p, (limit - read) or 10)
				thisread = len(next[0])
				read += thisread
				completed.append(next[0])
				if thisread:
					self.failUnlessEqual(
						last[0][-1][0], next[0][0][0] - 1,
						"first row(-1) of next failed to match the last row of the previous"
					)
					last = next
				elif next[1] != 0:
					# done
					break
			self.failUnlessEqual(read, limit)
			self.failUnlessEqual(list(range(-1, limit)), [
				x[0] for x in itertools.chain(*completed)
			])
	
	def test_insert(self):
		pass

	if 'gtx' in dir(__builtins__) and gtx.version_info >= (8,2,0):
		def test_copy_out(self):
			total = 0
			while total < 10000000:
				limit = random.randrange(500000)
				read = 0
				total += limit
				p = random_copy_get(limit)()
				last = ([-1], 1)
				completed = [last[0]]
				while True:
					next = random_read(p, (limit - read) or 10)
					next = ([int(x) for x in next[0]], next[1])
					thisread = len(next[0])
					read += thisread
					completed.append(next[0])
					if thisread:
						self.failUnlessEqual(
							last[0][-1], next[0][0] - 1,
							"first row(-1) of next failed to match the last row of the previous"
						)
						last = next
					elif next[1] != 0:
						# done
						break
				self.failUnlessEqual(read, limit)
				self.failUnlessEqual(
					list(range(-1, limit)),
					list(itertools.chain(*completed))
				)

	def test_copy_in(self):
		pass

if __name__ == '__main__':
	from types import ModuleType
	this = ModuleType("this")
	this.__dict__.update(globals())
	unittest.main(this)
