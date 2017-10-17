import logging
import argparse

import p4_autobuild

def add_watch(db, name):
  watch = p4_autobuild.BuildWatch(None, name)
  try:
    watch.insert(db)
    db.commit()
  except p4_autobuild.UniqueError, e:
    logging.error('A watch already exists with name %s' % watch.name)

def add_path(db, name, path):
  watch = p4_autobuild.BuildWatch.fetch_by_name(db, name)
  if watch is None:
    logging.error('No such watch: %s' % name)
    return

  db_path = p4_autobuild.P4Path.fetch_by_path(db, path)
  if db_path is None:
    p4_autobuild.P4Path(None, path).insert(db)
    db_path = p4_autobuild.P4Path.fetch_by_path(db, path)
  
  join = p4_autobuild.BuildWatchPath(watch.id, db_path.id)
  join.insert(db)
  db.commit()

def remove_path(db, name, path):
  watch = p4_autobuild.BuildWatch.fetch_by_name(db, name)
  if watch is None:
    logging.error('No such watch: %s' % name)
    return

  db_path = p4_autobuild.P4Path.fetch_by_path(db, path)
  if db_path is None:
    p4_autobuild.P4Path(None, path).insert(db)
    db_path = p4_autobuild.P4Path.fetch_by_path(db, path)
  
  join = p4_autobuild.BuildWatchPath(watch.id, db_path.id)
  join.delete(db)
  db.commit()

def list_watches(db):
  for watch in p4_autobuild.BuildWatch.fetch_all(db):
    print "%d: %s" % (watch.id, watch.name)

def show_watch(db, name):
  watch = p4_autobuild.BuildWatch.fetch_by_name(db, name)
  if watch is not None:
    print 'ID   : %d' % watch.id
    print 'Name : %s' % watch.name
    print 'Paths:'
    paths = p4_autobuild.P4Path.fetch_by_watch(db, watch)
    for path in paths:
      print '  %s' % path.path
  else:
    logging.error('No such watch: %s' % name)

logging.basicConfig()

parser = argparse.ArgumentParser()
parser.add_argument('--debug',
                    action='store_true',
                    help='Enable debug messages')
subparsers = parser.add_subparsers(dest='action',
                                   title='subcommands')

parser_add_watch = subparsers.add_parser('add-watch',
                                         help='Add a new watch',
                                         description='Adds a new watch')
parser_add_watch.add_argument('watch_name', help='The name of the watch')

parser_add_watch = subparsers.add_parser('add-path',
                                         help='Add a Perforce path to a watch',
                                         description='Add a Perforce path to a watch')
parser_add_watch.add_argument('watch_name', help='The name of the watch')
parser_add_watch.add_argument('path', help='The Perforce path to watch')

parser_remove_watch = subparsers.add_parser('remove-path',
                                            help='Remove a Perforce path from a watch',
                                            description='Remove a Perforce path from a watch')
parser_remove_watch.add_argument('watch_name', help='The name of the watch')
parser_remove_watch.add_argument('path', help='The Perforce path to watch')

parser_list_watch = subparsers.add_parser('list-watches',
                                          help='List all known watches',
                                          description='List all known watches')

parser_show_watch = subparsers.add_parser('show-watch',
                                          help="""Show the details of a watch
                                                  and the paths it watches""",
                                          description="""Show the details of a watch
                                                         and the paths it watches""")
parser_show_watch.add_argument('watch_name', help='The name of the watch')

args = parser.parse_args()

if args.debug:
  logging.getLogger().setLevel(logging.DEBUG)

db = p4_autobuild.DB()

if args.action == 'add-watch':
  add_watch(db, args.watch_name)
elif args.action == 'add-path':
  add_path(db, args.watch_name, args.path)
elif args.action == 'remove-path':
  remove_path(db, args.watch_name, args.path)
elif args.action == 'list-watches':
  list_watches(db)
elif args.action == 'show-watch':
  show_watch(db, args.watch_name)
else:
  logging.error('Unknown action: %s' % args.action)
