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


