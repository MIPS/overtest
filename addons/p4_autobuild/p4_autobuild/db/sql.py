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
class BoolColumnFormatter(object):
  def format(self, value):
    if value is None:
      return 'NULL'
    return 'true' if value else 'false'

class IntColumnFormatter(object):
  def format(self, value):
    if value is None:
      return 'NULL'
    return '%d' % value

class StringColumnFormatter(object):
  def format(self, value):
    if value is None:
      return 'NULL'
    return '\'%s\'' % value.replace('\'', '\'\'')

class AndCondition(object):
  def __init__(self, children):
    self.children = children

  def __str__(self):
    return ' AND '.join(str(x) for x in self.children)

class StrictEqualCondition(object):
  def __init__(self, stmt, lhs, rhs):
    self.stmt = stmt
    self.lhs = lhs
    self.rhs = rhs

  def __str__(self):
    rhs = self.rhs
    if rhs is None:
      return '{lhs} IS NULL'.format(lhs=self.lhs)
    rhs = self.stmt.columns[self.lhs].format(rhs)
    return '{lhs}={rhs}'.format(lhs=self.lhs, rhs=rhs)

class Select(object):
  def __init__(self, table):
    self.table = table
    self.columns = {}
    self.column_order = []
    self.where = None
    self.for_update = False
    self.order_by = None
    self.limit = None

  def add_column(self, name, formatter):
    self.column_order.append(name)
    self.columns[name] = formatter

  def add_hidden_column(self, name, formatter):
    self.columns[name] = formatter

  def set_limit(self, sql):
    self.limit = sql

  def set_order_by(self, sql):
    self.order_by = sql

  def set_where(self, condition):
    self.where = condition

  def _format_columns(self):
    assert self.column_order

    lst = []
    for name in self.column_order:
      lst.append(name)
    return ', '.join(lst)

  def _format_where(self):
    if self.where is None:
      return ''
    else:
      return ' WHERE {condition}'.format(condition=str(self.where))

  def __str__(self):
    columns = self._format_columns()
    where = self._format_where()
    s = 'SELECT {columns} FROM {table}{where}'.format(columns=columns, table=self.table, where=where)
    if self.order_by is not None:
      s += ' ORDER BY ' + self.order_by
    if self.for_update:
      s += ' FOR UPDATE'
    if self.limit is not None:
      s += ' LIMIT %d' % self.limit
    s += ';'
    return s

class Delete(Select):
  def __str__(self):
    where = self._format_where()
    s = 'DELETE FROM {table}{where};'.format(table=self.table, where=where)
    return s

class Update(object):
  def __init__(self, table):
    self.table = table
    self.columns = {}
    self.column_order = []
    self.values = {}
    self.where = None
    self.for_update = False

  def add_column(self, name, formatter):
    self.column_order.append(name)
    self.columns[name] = formatter

  def add_assign(self, name, value):
    self.values[name] = value

  def set_where(self, condition):
    self.where = condition

  def _format_assigns(self):
    assert self.column_order

    lst = []
    for name in self.column_order:
      if name in self.values:
        lst.append('{name}={value}'.format(name=name, value=self.columns[name].format(self.values[name])))
    return ', '.join(lst)

  def _format_where(self):
    if self.where is None:
      return ''
    else:
      return ' WHERE {condition}'.format(condition=str(self.where))

  def __str__(self):
    assigns = self._format_assigns()
    where = self._format_where()
    s = 'UPDATE {table} SET {assigns}{where};'.format(assigns=assigns, table=self.table, where=where)
    return s

class Insert(object):
  def __init__(self, table):
    self.table = table
    self.columns = {}
    self.column_order = []
    self.rows = []

  def add_column(self, name, formatter):
    self.column_order.append(name)
    self.columns[name] = formatter

  def add_row(self, row):
    assert len(row) == len(self.columns)
    self.rows.append(row)

  def _format_columns(self):
    assert self.column_order

    lst = []
    for name in self.column_order:
      lst.append(name)
    return ', '.join(lst)

  def _format_values(self):
    assert self.column_order

    lst = []
    for row in self.rows:
      row_txt = []
      for name, value in zip(self.column_order, row):
        row_txt.append(self.columns[name].format(value))
      lst.append('(%s)' % (', '.join(row_txt)))
    return ', '.join(lst)

  def __str__(self):
    columns = self._format_columns()
    values = self._format_values()
    s = 'INSERT INTO {table} ({columns}) VALUES {values}'.format(columns=columns, table=self.table, values=values)
    s += ';'
    return s

if __name__ == '__main__':
  sql = Select('bld_host_configs')
  sql.add_column ('fqdn',      StringColumnFormatter())
  sql.add_column ('smtp_fqdn', StringColumnFormatter())
  sql.add_column ('smtp_port', IntColumnFormatter())
  sql.set_order_by('fqdn DESC')
  sql.set_limit(100)
  print str(sql)
  sql.set_where (StrictEqualCondition(sql, 'fqdn', 'klmeta05.kl.imgtec.org'))
  print str(sql)
  sql = Update('bld_host_configs')
  sql.add_column ('fqdn',      StringColumnFormatter())
  sql.add_column ('smtp_fqdn', StringColumnFormatter())
  sql.add_column ('smtp_port', IntColumnFormatter())
  sql.add_assign ('smtp_fqdn', 'klmeta05.kl.imgtec.org')
  sql.add_assign ('smtp_port', 25)
  print str(sql)
  sql.set_where (StrictEqualCondition(sql, 'fqdn', 'klmeta05.kl.imgtec.org'))
  print str(sql)
  sql = Insert('bld_host_configs')
  sql.add_column ('fqdn',      StringColumnFormatter())
  sql.add_column ('smtp_fqdn', StringColumnFormatter())
  sql.add_column ('smtp_port', IntColumnFormatter())
  sql.add_row (('klmeta05.kl.imgtec.org', 'klmail01.kl.imgtec.org', 25))
  sql.add_row (('klmeta06.kl.imgtec.org', 'klmail01.kl.imgtec.org', 25))
  print str(sql)
  sql = Delete('bld_host_configs')
  sql.add_column ('fqdn',      StringColumnFormatter())
  sql.add_column ('smtp_fqdn', StringColumnFormatter())
  sql.add_column ('smtp_port', IntColumnFormatter())
  sql.set_where (StrictEqualCondition(sql, 'fqdn', 'klmeta05.kl.imgtec.org'))
  print str(sql)
