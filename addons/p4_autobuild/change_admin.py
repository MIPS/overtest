import logging
import argparse

import p4_autobuild

def _get_testrun(db, watch_name, changelist):
  watch = p4_autobuild.BuildWatch.fetch_by_name(db, watch_name)
  if watch is None:
    logging.error('No such watch: %s' % watch_name)
    return

  change = p4_autobuild.P4Change.fetch_by_watch_and_changelist(db, watch, changelist)
  if changelist is None:
    logging.error('No such change: @%d' % change)
    return

  if change.overtest_testrun_id is None:
    logging.error('Specified change has not completed')
    return

  return change, p4_autobuild.OvertestTestrun.fetch_by_id(db, change.overtest_testrun_id)

def renotify(db, watch_name, changelist):
  change, testrun = _get_testrun(db, watch_name, changelist)
  if testrun.notified:
    testrun.notified = False
    testrun.update(db)
    db.commit()

def retry(db, watch_name, changelist):
  change, testrun = _get_testrun(db, watch_name, changelist)
  change.overtest_testrun_id = None
  change.update(db)
  testrun.delete(db)
  db.commit()

def delete(db, watch_name, changelist):
  change, testrun = _get_testrun(db, watch_name, changelist)
  change.delete(db)
  testrun.delete(db)
  db.commit()

def list_all(db):
  pass_states = {None: 'Results pending', True: 'Passed', False: 'Failed'}

  changes = p4_autobuild.P4Change.fetch_all(db)
  for change in sorted(changes, key=lambda x: (x.watch_id, x.changelist)):
    watch = p4_autobuild.BuildWatch.fetch_by_id(db, change.watch_id)
    testrun = p4_autobuild.OvertestTestrun.fetch_by_id(db, change.overtest_testrun_id)
    print '{watch} @{changelist} {uname}'.format(watch=watch.name, changelist=change.changelist, uname=change.username)
    print '.. Testrun {testrun}'.format(testrun=testrun.id)
    print '.. {complete}'.format(complete='Completed' if testrun.completed else 'Incomplete')
    print '.. {passed}'.format(passed=pass_states[testrun.passed])
    print '.. {notified}'.format(notified='Notified subscribers' if testrun.notified else 'Notification pending')

def list_all_brief(db):
  pass_states = {None: 'Results pending', True: 'Passed', False: 'Failed'}

  changes = p4_autobuild.P4Change.fetch_all(db)
  for change in sorted(changes, key=lambda x: (x.watch_id, x.changelist)):
    watch = p4_autobuild.BuildWatch.fetch_by_id(db, change.watch_id)
    testrun = p4_autobuild.OvertestTestrun.fetch_by_id(db, change.overtest_testrun_id)
    state = 'Waiting'
    testrun_id = None
    if testrun is not None:
      testrun_id = testrun.id
      state = 'Running'
      if testrun.completed:
        if testrun.passed is True:
          state = 'Passed'
        elif testrun.passed is False:
          state = 'Failed'
    print '{watch} @{changelist} {uname} [{testrun}] {state}'.format(watch=watch.name, changelist=change.changelist, uname=change.username, testrun=testrun_id, state=state)

logging.basicConfig()

parser = argparse.ArgumentParser()
parser.add_argument('--debug',
                    action='store_true',
                    help='Enable debug messages')
subparsers = parser.add_subparsers(dest='action',
                                   title='subcommands')

parser_renotify = subparsers.add_parser('renotify',
                                        help='Clears the notified flag',
                                        description='Clears the notified flag')
parser_renotify.add_argument('watch_name', help='The watch to subscribe to')
parser_renotify.add_argument('changelist', type=int, help='The number of the changelist')

parser_retry = subparsers.add_parser('retry',
                                     help='Retry a build',
                                     description='Retry a build')
parser_retry.add_argument('watch_name', help='The watch to subscribe to')
parser_retry.add_argument('changelist', type=int, help='The number of the changelist')

parser_delete = subparsers.add_parser('delete',
                                      help='Delete a build',
                                      description='Delete a build')
parser_delete.add_argument('watch_name', help='The watch to subscribe to')
parser_delete.add_argument('changelist', type=int, help='The number of the changelist')

parser_list = subparsers.add_parser('list',
                                    help='List all builds',
                                    description='List all builds')

parser_list_brief = subparsers.add_parser('list-brief',
                                          help='List all builds',
                                          description='List all builds')

args = parser.parse_args()

if args.debug:
  logging.getLogger().setLevel(logging.DEBUG)

db = p4_autobuild.DB()

logging.warn('This script is intended for debugging purposes only')

if args.action == 'renotify':
  renotify(db, args.watch_name, args.changelist)
elif args.action == 'retry':
  retry(db, args.watch_name, args.changelist)
elif args.action == 'delete':
  delete(db, args.watch_name, args.changelist)
elif args.action == 'list':
  list_all(db)
elif args.action == 'list-brief':
  list_all_brief(db)
else:
  logging.error('Unknown action: %s' % args.action)
