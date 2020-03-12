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
import socket

import postgresql.exceptions

from p4_autobuild.db import DB
from p4_autobuild.db.sql import BoolColumnFormatter, IntColumnFormatter, StringColumnFormatter, \
                                StrictEqualCondition, AndCondition, \
                                Select, Update, Insert, Delete

logger = logging.getLogger(__name__)

class DBObject(object):
  @classmethod
  def _get_select_stem(cls):
    sql = Select(cls.table)
    sql = cls._add_columns(sql)
    return sql

  @classmethod
  def _select(cls, db, sql):
    return db._raw_execute(str(sql))._fetchall_as_object(cls)

  @classmethod
  def fetch_all(cls, db):
    sql = cls._get_select_stem()
    return cls._select(db, sql)

  def insert(self, db):
    sql = Insert(self.table)
    sql = self._add_insert_columns(sql)
    sql.add_row(self._make_insert_row())
    db._raw_execute(str(sql))

  def delete(self, db):
    sql = Delete(self.table)
    sql = self._add_columns(sql)
    sql.set_where(self._get_primary_key_condition(sql))
    db._raw_execute(str(sql))

  def lock(self, db):
    sql = self._get_select_stem()
    sql.set_where(self._get_primary_key_condition(sql))
    sql.for_update = True
    rows = self._select(db, sql)
    return rows[0] if len(rows) >= 1 else None

  @classmethod
  def _add_columns(cls, sql):
    """ Add columns to a SELECT or UPDATE statement """
    raise NotImplementedError()

  @classmethod
  def _add_insert_columns(cls, sql):
    """
    Add columns to a INSERT statement.
    This is often the same as _add_columns, possibly with the primary key removed
    """
    raise NotImplementedError()

  def _make_insert_row(self):
    """
    Make a row suitable for use with an INSERT statement build by _add_insert_columns
    """
    raise NotImplementedError()

  def _get_primary_key_condition(self, sql):
    """
    Get a condition that checks the primary key against this object
    """
    raise NotImplementedError()

class BuildHostConfig(DBObject):
  table = 'bld_host_configs'

  def __init__(self, *args):
    self.fqdn, self.smtp_fqdn, self.smtp_port = args

  @classmethod
  def _add_columns(cls, sql):
    sql.add_column ('fqdn',      StringColumnFormatter())
    sql.add_column ('smtp_fqdn', StringColumnFormatter())
    sql.add_column ('smtp_port', StringColumnFormatter())
    return sql

  @classmethod
  def fetch_by_fqdn(cls, db, fqdn):
    sql = cls._get_select_stem()
    sql.set_where(StrictEqualCondition(sql, 'fqdn', fqdn))
    config = cls._select(db, sql)
    return config[0] if len(config) >= 1 else None

  @classmethod
  def fetch_for_localhost(cls, db):
    fqdn = socket.getfqdn()
    logger.debug('Loading config for %s' % fqdn)
    cfg = cls.fetch_by_fqdn(db, fqdn)
    if cfg is None:
      logger.error('Config not found')
      raise KeyError('Host config for %s not found' % fqdn)
    return cfg

  def __repr__(self):
    return 'BuildHostConfig(\'%s\', \'%s\', %d)' % (self.fqdn, self.smtp_fqdn, self.smtp_port)

class BuildSubscriber(DBObject):
  table = 'bld_subscribers'

  def __init__(self, *args):
    self.id, self.email = args

  @classmethod
  def _add_columns(cls, sql):
    sql.add_column ('id',    IntColumnFormatter())
    sql.add_column ('email', StringColumnFormatter())
    return sql

  @classmethod
  def _add_insert_columns(cls, sql):
    sql.add_column ('email', StringColumnFormatter())
    return sql

  def _make_insert_row(self):
    assert self.id == None
    return (self.email,)

  @classmethod
  def fetch_by_email(cls, db, email):
    sql = cls._get_select_stem()
    sql.set_where(StrictEqualCondition(sql, 'email', email))
    rows = cls._select(db, sql)
    return rows[0] if len(rows) >= 1 else None

  @classmethod
  def fetch_by_watch(cls, db, watch):
    sql = Select('bld_subscribers_for_watch')
    sql.add_hidden_column ('watch_id', IntColumnFormatter())
    sql.add_column ('subscriber_id', IntColumnFormatter())
    sql.add_column ('email', StringColumnFormatter())
    sql.set_where (StrictEqualCondition(sql, 'watch_id', watch.id))
    return cls._select(db, sql)

  def __repr__(self):
    return 'BuildSubscriber(%s, \'%s\')' % (self.id, self.email)

class BuildWatch(DBObject):
  table = 'bld_watches'

  def __init__(self, *args):
    self.id, self.name = args

  def __repr__(self):
    return 'BuildWatch(%s, \'%s\')' % (self.id, self.name)

  @classmethod
  def _add_columns(cls, sql):
    sql.add_column ('id',   IntColumnFormatter())
    sql.add_column ('name', StringColumnFormatter())
    return sql

  @classmethod
  def _add_insert_columns(cls, sql):
    sql.add_column ('name', StringColumnFormatter())
    return sql

  def _make_insert_row(self):
    return (self.name,)

  @classmethod
  def fetch_by_id(cls, db, id_):
    sql = cls._get_select_stem()
    sql.set_where(StrictEqualCondition(sql, 'id', id_))
    rows = cls._select(db, sql)
    return rows[0] if len(rows) >= 1 else None

  @classmethod
  def fetch_by_name(cls, db, name):
    sql = cls._get_select_stem()
    sql.set_where(StrictEqualCondition(sql, 'name', name))
    rows = cls._select(db, sql)
    return rows[0] if len(rows) >= 1 else None

  @classmethod
  def fetch_by_subscriber(cls, db, user):
    sql = Select('bld_watches_for_subscriber')
    sql.add_hidden_column ('subscriber_id',   IntColumnFormatter())
    sql.add_column ('watch_id',   IntColumnFormatter())
    sql.add_column ('name', StringColumnFormatter())
    sql.set_where (StrictEqualCondition(sql, 'subscriber_id', user.id))
    return cls._select(db, sql)

class BuildSubscriberWatch(DBObject):
  table = 'bld_subscribers_watches'

  def __init__(self, *args):
    self.subscriber_id, self.watch_id = args

  def __repr__(self):
    return 'BuildSubscriberWatch(%s, \'%s\')' % (self.subscriber_id, self.watch_id)

  @classmethod
  def _add_columns(cls, sql):
    sql.add_column ('subscriber_id', IntColumnFormatter())
    sql.add_column ('watch_id', IntColumnFormatter())
    return sql

  @classmethod
  def _add_insert_columns(cls, sql):
    return cls._add_columns(sql)

  def _make_insert_row(self):
    return (self.subscriber_id, self.watch_id)

  def _get_primary_key_condition(self, sql):
    return AndCondition([StrictEqualCondition(sql, 'subscriber_id', self.subscriber_id),
                         StrictEqualCondition(sql, 'watch_id', self.watch_id)])

class BuildWatchPath(DBObject):
  table = 'bld_watches_paths'

  def __init__(self, *args):
    self.watch_id, self.path_id = args

  def __repr__(self):
    return 'BuildWatchPath(%s, \'%s\')' % (self.watch_id, self.path_id)

  @classmethod
  def _add_columns(cls, sql):
    sql.add_column ('watch_id', IntColumnFormatter())
    sql.add_column ('path_id', IntColumnFormatter())
    return sql

  @classmethod
  def _add_insert_columns(cls, sql):
    return cls._add_columns(sql)

  def _make_insert_row(self):
    return (self.watch_id, self.path_id)

  def _get_primary_key_condition(self, sql):
    return AndCondition([StrictEqualCondition(sql, 'watch_id', self.watch_id),
                         StrictEqualCondition(sql, 'path_id', self.path_id)])

class OvertestTestrun(DBObject):
  table = 'ovt_testrun'

  def __init__(self, *args):
    self.id, self.completed, self.passed, self.notified = args

  def __repr__(self):
    return 'OvertestTestrun(%s, %s, %s, %s)' % (self.id, self.completed, self.passed, self.notified)

  @classmethod
  def _add_columns(cls, sql):
    sql.add_column ('id',        IntColumnFormatter())
    sql.add_column ('completed', BoolColumnFormatter())
    sql.add_column ('passed',    BoolColumnFormatter())
    sql.add_column ('notified',  BoolColumnFormatter())
    return sql

  @classmethod
  def _add_insert_columns(cls, sql):
    return cls._add_columns(sql)

  def _get_primary_key_condition(self, sql):
    return StrictEqualCondition(sql, 'id', self.id)

  def _make_insert_row(self):
    return (self.id, self.completed, self.passed, self.notified)

  @classmethod
  def fetch_by_id(cls, db, id_):
    sql = cls._get_select_stem()
    sql.set_where(StrictEqualCondition(sql, 'id', id_))
    rows = cls._select(db, sql)
    return rows[0] if len(rows) >= 1 else None

  @classmethod
  def fetch_incomplete(cls, db):
    sql = cls._get_select_stem()
    sql.set_where(StrictEqualCondition(sql, 'completed', False))
    return cls._select(db, sql)

  @classmethod
  def fetch_unnotified(cls, db):
    sql = cls._get_select_stem()
    condition = AndCondition([StrictEqualCondition(sql, 'completed', True),
                              StrictEqualCondition(sql, 'notified', False),
                             ])
    sql.set_where(condition)
    return cls._select(db, sql)

  def update(self, db):
    sql = Update(self.table)
    sql = self._add_columns(sql)
    sql.set_where(self._get_primary_key_condition(sql))
    sql.add_assign('completed', self.completed)
    sql.add_assign('passed',    self.passed)
    sql.add_assign('notified',  self.notified)
    db._raw_execute(str(sql))

class P4Change(DBObject):
  table = 'p4_changes'

  def __init__(self, *args):
    self.changelist, self.username, self.watch_id, self.overtest_testrun_id = args

  def __repr__(self):
    return 'P4Change(%s, %s, %s, %s)' % (self.changelist, self.username, self.watch_id, self.overtest_testrun_id)

  @classmethod
  def _add_columns(cls, sql):
    sql.add_column ('changelist',          IntColumnFormatter())
    sql.add_column ('username',            StringColumnFormatter())
    sql.add_column ('watch_id',            IntColumnFormatter())
    sql.add_column ('overtest_testrun_id', IntColumnFormatter())
    return sql

  @classmethod
  def _add_insert_columns(cls, sql):
    return cls._add_columns(sql)

  def _get_primary_key_condition(self, sql):
    return AndCondition([StrictEqualCondition(sql, 'changelist', self.changelist),
                         StrictEqualCondition(sql, 'watch_id', self.watch_id)])

  def _make_insert_row(self):
    return (self.changelist, self.username, self.watch_id, self.overtest_testrun_id)

  @classmethod
  def fetch_by_watch_and_changelist(cls, db, watch, changelist):
    sql = cls._get_select_stem()
    sql.set_where(AndCondition([StrictEqualCondition(sql, 'watch_id', watch.id),
                                StrictEqualCondition(sql, 'changelist', changelist),
                               ]))
    rows = cls._select(db, sql)
    return rows[0] if len(rows) >= 1 else None

  @classmethod
  def fetch_by_overtest_testrun_id(cls, db, overtest_testrun_id):
    sql = cls._get_select_stem()
    sql.set_where(StrictEqualCondition(sql, 'overtest_testrun_id', overtest_testrun_id))
    rows = cls._select(db, sql)
    return rows[0] if len(rows) >= 1 else None

  @classmethod
  def fetch_max_changelist(cls, db):
    sql = cls._get_select_stem()
    sql.set_order_by('changelist DESC')
    sql.set_limit(1)
    rows = cls._select(db, sql)
    return rows[0] if len(rows) >= 1 else None

  @classmethod
  def fetch_unsubmitted(cls, db):
    sql = cls._get_select_stem()
    sql.set_where(StrictEqualCondition(sql, 'overtest_testrun_id', None))
    rows = cls._select(db, sql)
    return rows

  def update(self, db):
    sql = Update(self.table)
    sql = self._add_columns(sql)
    sql.set_where(self._get_primary_key_condition(sql))
    sql.add_assign('username', self.username)
    sql.add_assign('overtest_testrun_id', self.overtest_testrun_id)
    db._raw_execute(str(sql))

class P4Path(DBObject):
  table = 'p4_paths'

  def __init__(self, *args):
    self.id, self.path = args

  def __repr__(self):
    return 'P4Path(%s, \'%s\')' % (self.id, self.path)

  @classmethod
  def _add_columns(cls, sql):
    sql.add_column('id',   IntColumnFormatter())
    sql.add_column('path', StringColumnFormatter())
    return sql

  @classmethod
  def _add_insert_columns(cls, sql):
    sql.add_column('path', StringColumnFormatter())
    return sql

  def _make_insert_row(self):
    return (self.path,)

  @classmethod
  def fetch_by_path(cls, db, path):
    sql = cls._get_select_stem()
    sql.set_where(StrictEqualCondition(sql, 'path', path))
    rows = cls._select(db, sql)
    return rows[0] if len(rows) >= 1 else None

  @classmethod
  def fetch_by_watch(cls, db, watch):
    sql = Select('p4_paths_for_watch')
    sql.add_hidden_column ('watch_id',   IntColumnFormatter())
    sql.add_column ('path_id',   IntColumnFormatter())
    sql.add_column ('path', StringColumnFormatter())
    sql.set_where (StrictEqualCondition(sql, 'watch_id', watch.id))
    return cls._select(db, sql)

UniqueError = postgresql.exceptions.UniqueError
