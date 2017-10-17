# -*- encoding: utf-8 -*-
# $Id: api.py,v 1.3 2008/05/30 02:49:15 jwp Exp $
##
# copyright 2008, pg/python project.
# http://python.projects.postgresql.org
##
"""
GreenTrunk API
==============

pg_greentrunk is a Python API to the PostgreSQL RDBMS. It is designed to take
full advantage of the database elements provided by PostgreSQL to provide the
Python programmer with substantial convenience.

This module is used to define the GreenTrunk API. It creates a set of classes
that makes up the basic interfaces used to work with a PostgreSQL database.

Connection objects aren't required to be a part in any special class hierarchy.
Merely, the Python protocol described here *must be* supported. For instance, a
module object could be a connection to the database. However, it is recommended
that implementations inherit from these objects in order to benefit from the
provided doc-strings.

The examples herein will regularly refer to a ``gtx`` object; this object is the
`connection` instance--a GreenTrunk Connect(X)ion.


Exceptions
----------

For the most part, GreenTrunk tries to stay out of the databases' business. When
a database error occurs, it should be mapped to the corresponding exception in
``postgresql.exceptions`` and raised--the exceptions module is provided by the
`pkg:pg_foundation` package. In the cases of fatal errors, panics, or unexpected
closures, the same exception must be raised anytime an operation is enacted on
the connection until the connection is explicitly closed.

When a connection is closed and an operation is attempted on the connection--
other than ``connect``, the `postgresql.exceptions.ConnectionDoesNotExistError`
error must be raised.

When a connection's link is somehow lost on an operation, the
`postgresql.exceptions.ConnectionFailureError` exception should be raised. If
exception chains are supported by the Python implementation, it should chain the
literal exception onto the ``ConnectionFailureError`` instance. If no explicit
exception caused the loss, then the ``ConnectionFailureError`` error message
should describe the symptom indicating the loss.
"""

class query(object):
	"""
	A `query` object is an interface to a prepared statement. `query` objects are
	normally created by invoking `connection.query`.
	"""

	def __del__(self):
		"""
		Close the prepared statement on the server as the only reference to its
		existence is gone. This occurs *iff* the query was prepared by the client.
		"""

	def __call__(self, *args):
		"""
		Execute the prepared statement with the given arguments as parameters. If
		the query returns rows, a cursor object should be returned, otherwise a
		resulthandle object.

		Usage:

		>>> q=gtx.query("SELECT table_name FROM information_schema.tables WHERE
		... table_schema = $1")
		>>> q('public')
		<cursor object>
		"""

	def first(self, *args):
		"""
		Execute the prepared statement with the given arguments as parameters. If
		the query returns rows with multiple columns, return the first row. If the
		query returns rows with a single column, return the first column in the
		first row. If the query does not return rows at all, return the count or
		`None` if no count exists in the completion message. Usage:

		>>> gtx.query("SELECT * FROM ttable WHERE key = $1").first("somekey")
		('somekey', 'somevalue')
		"""

	def load(self, iterable):
		"""
		Given an iterable, `iterable`, feed the produced parameters to the query.
		This is a bulk-loading interface for parameterized queries.

		Effectively, it is equivalent to:
		
		>>> q = gtx.query(sql)
		>>> for i in iterable:
		...  q(*i)

		Its purpose is to allow the implementation to take advantage of the
		knowledge that a series of parameters are to be loaded.
		"""

	def __invert__(self):
		"""
		Shorthand for a call to the first() method without any arguments.
		Useful for resolving static queries. Example usage:

		>>> ~gtx.query("INSERT INTO ttable VALUES ('value')")
		1
		>>> ~gtx.query("SELECT 'somestring'")
		'somestring'
		"""

	def close(self):
		"""
		Close the prepraed statement releasing resources associated with it.
		"""

	def prepare(self):
		"""
		Prepare the already instantiated query for use. This method would only be
		used if the query were closed at some point.
		"""

	def reprepare(self):
		"""
		Shorthand for ``close`` then ``prepare``.
		"""

class cursor(object):
	"""
	A `cursor` object is an interface to a sequence of tuples(rows). A result set.
	Cursors publish a file-like interface for reading tuples from the database.

	`cursor` objects are created by invoking `query` objects or by calling
	`connection.cursor` with the declared cursor's name.
	"""

	def read(self, quantity = -1):
		"""
		Read the specified number of tuples and return them in a list.
		This advances the cursor's position.
		"""

	def close(self):
		"""
		Close the cursor to release its resources.
		"""

	def __next__(self):
		"""
		Get the next tuple in the cursor. Advances the position by one.
		"""
	next = __next__

	def seek(self, offset, whence = 0):
		"""
		Set the cursor's position to the given offset with respect to the
		whence parameter.

		Whence values:

		 ``0``
		  Absolute.
		 ``1``
		  Relative.
		 ``2``
		  Absolute from end.
		"""
	
	def scroll(self, rows):
		"""
		Set the cursor's position relative to the current position.
		Negative numbers can be used to scroll backwards.

		This is a convenient interface to `seek` with a relative whence(``1``).
		"""

	def __getitem__(self, idx):
		"""
		Get the rows at the given absolute position.
		"""

class proc(object):
	"""
	A `proc` object is an interface to a stored procedure. A `proc` object is
	created by `connection.proc`.
	"""

	def __call__(self, *args, **kw):
		"""
		Execute the procedure with the given arguments. If keyword arguments are
		passed they must be mapped to the argument whose name matches the key. If
		any positional arguments are given, they must fill in any gaps created by
		the filled keyword arguments. If too few or too many arguments are given,
		a TypeError must be raised. If a keyword argument is passed where the
		procedure does not have a corresponding argument name, then, likewise, a
		TypeError must be raised.
		"""

class xact(object):
	"""
	A xact object is the connection's transaction manager. It is already
	instantiated for every connection. It keeps the state of the transaction and
	provides methods for managing the state thereof.

	Normal usage would merely entail the use of the with-statement::

		with gtx.xact:
		...
	
	Or, in cases where two-phase commit is desired::

		with gtx.xact('gid'):
		...
	"""

	failed = property(
		doc = "bool instance stating if the current transaction " \
		"has failed due to an error." \
		" `None` if not in a transaction block."
	)
	closed = property(
		doc = "`bool` stating if there is an open transaction block."
	)

	def start(self):
		"""
		Start a transaction block. If a transaction block has already been
		started, set a savepoint.
		``start``, ``begin``, and ``__enter__`` are synonyms.
		"""
	__enter__ = begin = start

	def commit(self):
		"""
		Commit the transaction block, release a savepoint, or prepare the
		transaction for commit. If the number of running transactions is greater
		than one, then the corresponding savepoint is released. If no savepoints
		are set and the transaction is configured with a 'gid', then the
		transaction is prepared instead of committed, otherwise the transaction is
		simply committed.
		"""

	def rollback(self):
		"""
		Abort the current transaction or rollback to the last started savepoint.
		`rollback` and `abort` are synonyms.
		"""
	abort = rollback

	def restart(self):
		"""
		Abort and start the transaction or savepoint.
		"""

	def checkpoint(self):
		"""
		Commit and start a transaction block or savepoint. Not to be confused with
		the effect of the CHECKPOINT command.
		"""

	def __call__(self, gid = None, isolation = None, readonly = None):
		"""
		Initialize the transaction using parameters and return self to support a
		convenient with-statement syntax.

		The configuration only applies to transaction blocks as savepoints have no 
		parameters to be configured.

		If the `gid`, the first keyword parameter, is configured, the transaction
		manager will issue a ``PREPARE TRANSACTION`` with the specified identifier
		instead of a ``COMMIT``.

		If `isolation` is specified, the ``START TRANSACTION`` will include it as
		the ``ISOLATION LEVEL``. This must be a character string.

		If the `readonly` parameter is specified, the transaction block will be
		started in the ``READ ONLY`` mode if True, and ``READ WRITE`` mode if False.
		If `None`, neither ``READ ONLY`` or ``READ WRITE`` will be specified.

		Read-only transaction::

			>>> with gtx.xact(readonly = True):
			...

		Read committed isolation::

			>>> with gtx.xact(isolation = 'READ COMMITTED'):
			...

		Database configured defaults apply to all `xact` operations.
		"""

	def __context__(self):
		'Return self'

	def __exit__(self, typ, obj, tb):
		"""
		Commit the transaction, or abort if the given exception is not `None`. If
		the transaction level is greater than one, then the savepoint
		corresponding to the current level will be released or rolled back in
		cases of an exception.

		If an exception was raised, then the return value must indicate the need
		to further raise the exception, unless the exception is an
		`postgresql.exceptions.AbortTransaction`. In which case, the transaction
		will be rolled back accordingly, but the no exception will be raised.
		"""
	
	def commit_prepared(self, gid):
		"""
		Commit the prepared transaction with the given `gid`.
		"""
	
	def rollback_prepared(self, *gids):
		"""
		Rollback the prepared transaction with the given `gid`.
		"""

	prepared = property(
		doc = \
		"""
		A sequence of available prepared transactions for the current user on the
		current database. This is intended to be more relavent for the current
		context than selecting the contents of ``pg_prepared_xacts``. So, the view
		*must* be limited to those of the current database, and those which the
		user can commit.
		"""
	)

class settings(object):
	"""
	A mapping interface to the session's settings. This dictionary-like object
	provides a direct interface to ``SHOW`` or ``SET`` commands. Identifiers and
	values need not be quoted specially as the implementation must do that work
	for the user.
	"""

	def __getitem__(self, key):
		"""
		Return the setting corresponding to the given key. The result should be
		consistent with what the ``SHOW`` command returns. If the key does not
		exist, raise a KeyError.
		"""

	def __setitem__(self, key, value):
		"""
		Set the setting with the given key to the given value. The action should
		be consistent with the effect of the ``SET`` command.
		"""

	def __call__(self, **kw):
		"""
		Configure settings for the next established context and return the
		settings object. This is normally used in conjunction with a
		with-statement:

		>>> with gtx.settings(search_path = 'local,public'):
		...

		When called, the settings' object will configure itself to use the given
		settings for the duration of the block, when the block exits, the previous
		settings will be restored.

		If a configuration has already been stored when invoked, the old
		configuration will be overwritten. Users are expected to set the
		configuration immediately.
		"""

	def __enter__(self):
		"""
		Set the settings configured using the __call__ method.

		If nothing has been configured, do nothing.
		"""

	def __exit__(self, exc, val, tb):
		"""
		Immediately restore the settings if the connection is not in an error
		state. Otherwise, make the restoration pending until the state is
		corrected.
		"""

	def get(self, key, default = None):
		"""
		Get the setting with the corresponding key. If the setting does not exist,
		return the `default`.
		"""
	
	def getset(self, keys):
		"""
		Return a dictionary containing the key-value pairs of the requested
		settings. If *any* of the keys do not exist, a `KeyError` must be raised
		with the set of keys that did not exist.
		"""

	def update(self, mapping):
		"""
		For each key-value pair, incur the effect of the `__setitem__` method.
		"""

	def iterkeys(self):
		"""
		Return an iterator to all of the settings' keys.
		This method is provided for compatibility with dictionary objects.
		"""
	
	def keys(self):
		"""
		Return an iterator to all of the settings' keys.
		"""
	
	def itervalues(self):
		"""
		Return an iterator to all of the settings' values.
		This method is provided for compatibility with dictionary objects.
		"""

	def values(self):
		"""
		Return an iterator to all of the settings' values.
		"""

	def items(self):
		"""
		Return an iterator to all of the setting value pairs.
		"""

	def iteritems(self):
		"""
		Return an iterator to all of the setting value pairs.
		This method is provided for compatibility with dictionary objects.
		"""

	def subscribe(self, key, callback):
		"""
		Subscribe to changes of the setting using the callback. When the setting
		is changed, the callback will be invoked with the connection, the key,
		and the new value. If the old value is locally cached, its value will
		still be available for inspection, but there is no guarantee.
		If `None` is passed as the key, the callback will be called whenever any
		setting is remotely changed.

		>>> def watch(connection, key, newval):
		...
		>>> gtx.settings.subscribe('TimeZone', watch)
		"""

	def unsubscribe(self, key, callback):
		"""
		Stop listening for changes to a setting. The setting name(`key`), and the
		callback used to subscribe must be given again for successful termination
		of the subscription.

		>>> gtx.settings.unsubscribe('TimeZone', watch)
		"""

	path = property(
		doc = \
		"""
		An interface to a structured ``search_path`` setting:

		>>> gtx.settings.path
		['public', '$user']

		It may also be used to set the path:

		>>> gtx.settings.path = ('public', 'tools')
		"""
	)

class connection(object):
	"""
	The connection interface.
	"""

	def query(self, sql, *default_args, **kw):
		"""
		Create a new `.query` instance that provides an interface to the prepared statement.

		Given a single SQL statement, and optional default query arguments, create the
		prepared statement. The object returned is the interface to the
		prepared statement.

		The default arguments fill in the query's positional parameters.

		The ``title`` keyword argument is only used to help identify queries.
		The given value will be set to the query object's 'title' attribute.
		It is analogous to a function name.

		The ``prepare`` keyword argument tells the driver whether or not to actually
		prepare the query when it is instantiated. When `False`, defer preparation
		until execution or until it is explicitly ordered to prepare.

		>>> q = gtx.query("SELECT 1")
		>>> p = q()
		>>> p.next()
		(1,)

		It allows default arguments to be configured:

		>>> q = gtx.query("SELECT $1::int", 1)
		>>> q().next()
		(1,)

		And they are overrideable:

		>>> q(2).next()
		(2,)
		"""

	def cquery(self, sql, *default_args, **kw):
		"""
		Exactly like `query`, but cache the created `.query` object using the
		given `sql` as the key. If the same `sql` is given again, look it up and
		return the existing `.query` object instead of creating a new one.
		"""

	def statement(self, statement_id, *default_args, **kw):
		"""
		Create a `.query` object that was already prepared on the server. The distinction
		between this and a regular query is that it must be explicitly closed if it is no
		longer desired, and it is instantiated using the statement identifier as
		opposed to the SQL statement itself.

		If no ``title`` keyword is given, it will default to the statement_id.
		"""
	
	def cursor(self, cursor_id):
		"""
		Create a `.cursor` object from the given `cursor_id` that was already declared
		on the server.
		
		`.cursor` object created this way must *not* be closed when the object is garbage
		collected. Rather, the user must explicitly close it for the server
		resources to be released. This is in contrast to `.cursor` object that
		are created by invoking a `.query` object.
		"""
	
	def proc(self, proc_id):
		"""
		Create a reference to a stored procedure on the database. The given
		identifier can be either an Oid or a valid ``regprocedure`` string pointing at
		the desired function.

		The `proc_id` given can be either an ``Oid``, or a ``regprocedure`` identifier.

		>>> p = gtx.proc('version()')
		>>> p()
		u'PostgreSQL 8.3.0'

		>>> ~gtx.query("select oid from pg_proc where proname = 'generate_series'")
		1069
		>>> p = gtx.proc(1069)
		>>> list(p(1,5))
		[1, 2, 3, 4, 5]
		"""

	def connect(self):
		"""
		Establish the connection to the server. Does nothing if the connection is
		already established.
		"""

	def close(self):
		"""
		Close the connection. Does nothing if the connection is already closed.
		"""

	def reconnect(self):
		"""
		Method drawing the effect of ``close`` then ``connect``.
		"""

	def reset(self):
		"""
		Reset as much connection configuration as possible.

		Issues a ``RESET ALL`` to the database. If the database supports removing
		temporary tables created in the session, then remove them. Reapply
		initial configuration settings such as path. If inside a transaction
		block when called, reset the transaction state using the `reset`
		method on the connection's transaction manager, `xact`.

		The purpose behind this method is to provide a soft-reconnect method that
		reinitializes the connection into its original state. One obvious use of this
		would be in a connection pool where the connection is done being used.
		"""

	def __nonzero__(self):
		"""
		Returns `True` if there are no known error conditions that would impede an
		action, otherwise `False`.

		If the connection is in a failed transaction block, this must be `False`.
		If the connection is closed, this must be `False`.

		>>> bool(con) in (True, False)
		True
		"""

	def __enter__(self):
		"""
		Synonym to `connect` for with-statement support.
		"""

	def __exit__(self, typ, obj, tb):
		"""
		Closes the connection and returns `True` when an exception is passed in,
		`False` when `None`.

		If the connection has any operations queued or running, abort them.
		"""

	def __context__(self):
		"""
		Returns the connection object.
		"""

	def execute(sql):
		"""
		Execute an arbitrary block of SQL. Always returns `None` and raises an
		exception on error.
		"""

	type = property(
		doc = """
		`type` is a property providing the name of the database type. 'PostgreSQL'
		would be the usual case. However, other "kinds" of Postgres exist in the
		wild. Greenplum for example.
		"""
	)

	version_info = property(
		doc = """
		A version tuple of the database software similar Python's `sys.version_info`.

		>>> gtx.version_info
		(8, 1, 3, '', 0)
		"""
	)

	closed = property(
		doc = """
		A property that indicates whether the connection is open. If the connection
		is not open, then accessing closed will return True. If the connection is
		open, closed with return False.

		Additionally, setting it to `True` or `False` can open and close the
		connection. If the value set is not `True` or `False`, a `ValueError` must be
		raised.

		>>> gtx.closed
		True
		"""
	)

	user = property(
		doc = """
		A property that provides an interface to "SELECT current_user", ``SET
		ROLE``, and ``RESET ROLE``. When the attribute is resolved, the current user will
		be given as a character string(unicode). When the attribute is set, it will
		issue a ``SET ROLE`` command to the server, changing the session's user. When
		the attribute is deleted, a ``RESET ROLE`` command will be issued to the
		server.
		"""
	)

	xact = xact()
	settings = settings()

if __name__ == '__main__':
	help('postgresql.protocol.greentrunk.abstract')

__docformat__ = 'reStructuredText'
##
# vim: ts=3:sw=3:noet:
