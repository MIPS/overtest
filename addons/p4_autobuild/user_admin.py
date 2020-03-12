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
import argparse

import p4_autobuild

def add_user(db, email):
  subscriber = p4_autobuild.BuildSubscriber(None, email)
  try:
    subscriber.insert(db)
    db.commit()
  except p4_autobuild.UniqueError, e:
    logging.error('A user already exists with email address %s' % subscriber.email)

def subscribe(db, email, watch):
  user = p4_autobuild.BuildSubscriber.fetch_by_email(db, email)
  if user is None:
    logging.error('No such user: %s' % email)
    return

  watch = p4_autobuild.BuildWatch.fetch_by_name(db, watch)
  if watch is None:
    logging.error('No such watch: %s' % watch)
    return
  
  join = p4_autobuild.BuildSubscriberWatch(user.id, watch.id)
  join.insert(db)
  db.commit()

def unsubscribe(db, email, watch):
  user = p4_autobuild.BuildSubscriber.fetch_by_email(db, email)
  if user is None:
    logging.error('No such user: %s' % email)
    return

  watch = p4_autobuild.BuildWatch.fetch_by_name(db, watch)
  if watch is None:
    logging.error('No such watch: %s' % watch)
    return
  
  join = p4_autobuild.BuildSubscriberWatch(user.id, watch.id)
  join.delete(db)
  db.commit()

def list_users(db):
  for user in p4_autobuild.BuildSubscriber.fetch_all(db):
    print "%d: %s" % (user.id, user.email)

def show_user(db, email):
  user = p4_autobuild.BuildSubscriber.fetch_by_email(db, email)
  if user is not None:
    print 'ID   : %d' % user.id
    print 'Email: %s' % user.email
    print 'Watching:'
    watches = p4_autobuild.BuildWatch.fetch_by_subscriber(db, user)
    for watch in watches:
      print '  %s' % watch.name
  else:
    logging.error('No such user: %s' % email)

logging.basicConfig()

parser = argparse.ArgumentParser()
parser.add_argument('--debug',
                    action='store_true',
                    help='Enable debug messages')
subparsers = parser.add_subparsers(dest='action',
                                   title='subcommands')

parser_add_user = subparsers.add_parser('add-user',
                                        help='Add a new user.',
                                        description='Adds a new user')
parser_add_user.add_argument('email', help='The email address of the user')

parser_subscribe = subparsers.add_parser('subscribe',
                                         help='Subscribe a user to a watch',
                                         description='Subscribes a user to a watch')
parser_subscribe.add_argument('email', help='The email address of the user')
parser_subscribe.add_argument('watch_name', help='The watch to subscribe to')

parser_unsubscribe = subparsers.add_parser('unsubscribe',
                                         help='Unsubscribe a user from a watch',
                                         description='Unsubscribes a user from a watch')
parser_unsubscribe.add_argument('email', help='The email address of the user')
parser_unsubscribe.add_argument('watch_name', help='The watch to unsubscribe from')

parser_list_users = subparsers.add_parser('list-users',
                                          help='List all known users',
                                          description='List all known users')

parser_show_user = subparsers.add_parser('show-user',
                                         help="""Show the details for a user and
                                                 the watches they are subscribed to""",
                                         description="""Show the details for a user and
                                                        the watches they are subscribed to""")
parser_show_user.add_argument('email', help='The email address of the user')

args = parser.parse_args()

if args.debug:
  logging.getLogger().setLevel(logging.DEBUG)

db = p4_autobuild.DB()

if args.action == 'add-user':
  add_user(db, args.email)
elif args.action == 'subscribe':
  subscribe(db, args.email, args.watch_name)
elif args.action == 'unsubscribe':
  unsubscribe(db, args.email, args.watch_name)
elif args.action == 'list-users':
  list_users(db)
elif args.action == 'show-user':
  show_user(db, args.email)
else:
  logging.error('Unknown action: %s' % args.action)
