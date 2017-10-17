import argparse
import logging
import os
import pprint
import subprocess
import textwrap

import p4_autobuild
from p4_autobuild import BuildWatch, P4Path, P4Change
from P4 import P4

def p4_init(user):
  p4c = P4()
  p4c.port = 'klperforcebf:1666' # Don't use the FQDN! Ops have the details but the buildfarm server doesnt work properly with a FQDN.
  if user != 'xbuild.meta':
    logger.warn('Running using %s\'s credentials. This breaches the SCCM policy' % user)
  p4c.user = user
  p4c.client = 'bf_xbuild.meta_autobuild_scheduler_view_ws'
  p4c.connect()
  p4_make_workspace(p4c)
  return p4c

def p4_make_workspace(p4c):
  client = p4c.fetch_client(p4c.client)
  client['Description'] = textwrap.dedent(
    """
    This workspace provides a view with which
    overtest/addons/p4_autobuild/schedule.py can query perforce for any changes
    to watched projects since the last scan. As such, it does not matter what
    Root is (but perforce complains if it is not supplied) since the only command
    executed is 'p4 changes' using depot paths.

    This workspace is regenerated on each run of schedule.py so any changes to
    this workspace will be lost. This workspace is not deleted after use in
    case of races between multiple instances. Do not delete it manually.

    The view is very general to simplify the generation of this workspace.
    Perforce will enforce the actual permissions granted to {user}
    """.format(user=p4c.user))
  client['ServerID'] = 'klperforcebf'
  client['Host'] = ''
  client['View'] = ['//meta/... //%s/meta/...' % p4c.client]
  client['Root'] = '/path/to/nowhere'
  logging.debug('Client:')
  logging.debug(pprint.pformat(client))
  p4c.save_client(client)

def p4_changes(p4c, watch_paths):
  logging.debug('p4 changes %s' % (' '.join(watch_paths)))
  # Don't run 'p4 changes' without any paths
  if not watch_paths:
    logging.debug('.. no paths, not executing')
    raise StopIteration()

  changes = p4c.run_changes(*watch_paths)
  for change in changes:
    # Weed out pending numbered changelists
    if change['status'] != 'submitted':
      continue
    change['change'] = int(change['change'])
    yield change

logging.basicConfig()

parser = argparse.ArgumentParser(description="""
Schedule any new changes for all watches

When adding a new watch for a long-running project, it is advisable to run this
script with --start-from with a recent changelist number to avoid scheduling the
entirety of the project history.
""")
parser.add_argument('--debug',
                    action='store_true',
                    help='Enable debug messages')
parser.add_argument('--user',
                    default='xbuild.meta',
                    help=argparse.SUPPRESS)
parser.add_argument('--start-from',
                    type=int,
                    default=None,
                    help="""Limit search to commits after the specified changelist.
                    If not given, then the most recently scheduled changelist number
                    will be used.
                    """)

args = parser.parse_args()

if args.debug:
  logging.getLogger().setLevel(logging.DEBUG)

logger = logging.getLogger()
db = p4_autobuild.DB()
p4c = p4_init(args.user)

begin = args.start_from
if begin is None:
  change = P4Change.fetch_max_changelist(db)
  begin = change.changelist + 1 if change is not None else 0
logger.info('Scan from @%d' % begin)

for watch in BuildWatch.fetch_all(db):
  logging.debug('Scanning %s' % watch.name)
  watch_paths = []
  for path in P4Path.fetch_by_watch(db, watch):
    watch_paths.append('%s@%d,now' % (path.path, begin))

  for change in p4_changes(p4c, watch_paths):
    print '@%d %s %s' % (change['change'], change['user'], change['desc']) 
    try:
      P4Change(change['change'], change['user'], watch.id, None).insert(db)
      db.commit()
    except p4_autobuild.UniqueError, e:
      print '.. already scheduled'
      db.rollback()
    else:
      print '.. scheduled'
logging.debug('Finished')
