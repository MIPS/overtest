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
