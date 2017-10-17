import argparse
import logging
import os
import subprocess

import p4_autobuild
import p4_autobuild.overtest

logging.basicConfig()

parser = argparse.ArgumentParser(description="""
The bridge to overtest.
""")
parser.add_argument('--debug',
                    action='store_true',
                    help='Enable debug messages')
subparsers = parser.add_subparsers(dest='action',
                                   title='subcommands')

parser_submit_scheduled = subparsers.add_parser('submit-scheduled',
                                                help='Submit any scheduled builds',
                                                description='Submit any scheduled builds')

parser_reap_results = subparsers.add_parser('reap-results',
                                            help='Reap results',
                                            description='Reap results')

args = parser.parse_args()

if args.debug:
  logging.getLogger().setLevel(logging.DEBUG)

logger = logging.getLogger()
db = p4_autobuild.DB()

if args.action == 'submit-scheduled':
  p4_autobuild.overtest.submit_scheduled(db)
elif args.action == 'reap-results':
  p4_autobuild.overtest.reap_results(db)
  p4_autobuild.overtest.send_notifications(db)
else:
  logging.error('Unknown action: %s' % args.action)
