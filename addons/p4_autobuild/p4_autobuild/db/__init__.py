#  Copyright (C) 2012-2020 MIPS Tech LLC
#  Written by Matthew Fortune <matthew.fortune@imgtec.com> and
#  Daniel Sanders <daniel.sanders@imgtec.com>
#  This file is part of Overtest.
#
#  Overtest is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3, or (at your option)
#  any later version.
#
#  Overtest is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with overtest; see the file COPYING.  If not, write to the Free
#  Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
#  02110-1301, USA.
import logging

import postgresql.interface.proboscis.dbapi2 as dbapi2
import postgresql.strings as pg_str
import postgresql.exceptions

logger = logging.getLogger(__name__)

class DB(object):
  def __init__(self):
    self.connection = dbapi2.connect( host="overtest.le.imgtec.org", port=5432, database="perforce_autobuild", user="overtest", password="overtest")

  def _raw_execute(self, sql):
    logger.info('DB._raw_execute: %s' % sql)
    cursor = Cursor(self.connection.cursor())
    cursor._raw_execute(sql)
    return cursor

  def commit(self):
    logger.info('DB: Commit Transaction')
    self.connection.commit()

  def rollback(self):
    logger.info('DB: Rollback Transaction')
    self.connection.rollback()

class Cursor(object):
  def __init__(self, cursor):
    self.cursor = cursor

  def _raw_execute(self, sql):
    self.cursor.execute(sql)

  def fetch_all(self):
    return self.cursor.fetchall()

  def _fetchall_as_object(self, cls):
    return [cls(*x) for x in self.fetch_all()]


