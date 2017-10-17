import email.message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import itertools
import logging
import os
import pprint
import smtplib
import subprocess
import textwrap
import yaml

import p4_autobuild.watch_handlers
from p4_autobuild import BuildWatch, P4Path, P4Change, OvertestTestrun, BuildHostConfig, BuildSubscriber

logger = logging.getLogger(__name__)

def submit_scheduled(db):
  for change in P4Change.fetch_unsubmitted(db):
    print '@%d %s' % (change.changelist, change.username)
    watch = BuildWatch.fetch_by_id(db, change.watch_id)
    try:
      p4_autobuild.watch_handlers.submit(db, watch, change)
    except p4_autobuild.watch_handlers.HandlerException, e:
      logger.error('Error submitting build: %s' % e)

def _get_results(testrunid):
  cmd = ['python', 'overtest.py', '--export', '--schema=Results', '--testrunid=%d' % testrunid]
  workdir = os.path.join(os.path.dirname(__file__), "..", "..", "..")
  child = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=workdir)
  stdout, stderr = child.communicate()
  return yaml.load(stdout)

def reap_results(db):
  for testrun in OvertestTestrun.fetch_incomplete(db):
    logging.info('Inspecting state of testrun %d' % testrun.id)
    results = _get_results(testrun.id)
    logging.debug(pprint.pformat(results))
    if results['status'] in ('READYTOCHECK', 'CHECKED', 'HOSTALLOCATED', 'RUNNING',
                             'ABORTING', 'ARCHIVING', 'DELETING', 'EXTERNAL',
                             'READYTODELETE', 'READYTOARCHIVE'):
      logging.info('.. still in progress (and progressing) [%s]' % results['status'])
    elif results['status'] in ('PAUSED', 'CREATION'):
      logging.info('.. still in progress (and not progressing) [%s]' % results['status'])
    elif results['status'] in ('ALLOCATIONFAILED', 'CHECKFAILED', 'ABORTED'):
      logging.info('.. failed [%s]' % results['status'])
      testrun.completed = True
      testrun.passed = False
      testrun.update(db)
      db.commit()
    elif results['status'] in ('COMPLETED', 'ARCHIVED'):
      logging.info('.. failed [%s]' % results['status'])
      testrun.completed = True
      testrun.passed = True
      testrun.update(db)
      db.commit()

def _get_notification_data(db, testrun):
  change = P4Change.fetch_by_overtest_testrun_id(db, testrun.id)
  if change is None:
    logger.debug('Reached unreachable state. Someone has tampered with the p4_changes table')
    logger.debug('Recovering by deleting testrun')
    testrun.delete(db)
    db.commit()
    return None
  watch = BuildWatch.fetch_by_id(db, change.watch_id)
  subscribers = BuildSubscriber.fetch_by_watch(db, watch)
  return watch, change, subscribers

def _make_pass_notification(db, pass_data):
  tbody = []
  recipients = set()
  for group_key, group_data in itertools.groupby(pass_data, key=lambda x:x[1].name):
    print group_key
    for testrun, watch, change, subscribers in group_data:
      print testrun, watch
      tbody.append((watch.name, change.changelist, change.username, 'http://overtest.le.imgtec.org/viewtestrun.php?testrunid=%d' % testrun.id))
    recipients.update([x.email for x in subscribers])
  recipients = list(recipients)

  subject_template = '[Perforce Autobuilder] Summary of recent {watch} passes'
  text_template = """
  The autobuilder has discovered that the following testruns have passed.
  
  Watch Changelist User OvertestLink
  {tbody}

  You have received this email because you are watching one of the projects mentioned
  in the above table. Future versions of the autobuilder will separate projects
  into separate emails.
  """
  text_template = textwrap.dedent(text_template).strip('\n')
  html_template = """
  <p>The autobuilder has discovered that the following testruns have passed.</p>

  <table>
   <tr><th>Watch</th><th>Changelist</th><th>User</th><th>Overtest Link</th><tr>
   {tbody}
  </table>

  <p>You have received this email because you are watching one of the projects mentioned
  in the above table. Future versions of the autobuilder will separate projects
  into separate emails.</p>
  """
  html_template = textwrap.dedent(html_template).strip('\n')
  msg = MIMEMultipart('alternative')
  msg['From'] = 'overtest@imgtec.com'
  msg['Subject'] = subject_template.format(watch=watch.name)
  msg['X-Auto-Response-Suppress'] = 'OOF' # Stop autoresponders replying

  text_tbody = [', '.join(str(x) for x in row) for row in tbody]
  text_tbody = '\n'.join('%s' % row for row in text_tbody)

  html_tbody = ['</td><td>'.join(str(x) for x in row) for row in tbody]
  html_tbody = '<tr>%s</tr>' % ('</tr>\n<tr>'.join('<td>%s</td>' % row for row in html_tbody))

  part1 = MIMEText(text_template.format(tbody=text_tbody), 'plain')
  part2 = MIMEText(html_template.format(tbody=html_tbody), 'html')

  msg.attach(part1)
  msg.attach(part2)

  msg['To'] = ', '.join(recipients)
  return recipients, msg

def _make_failure_notification(db, testrun, subscribers, watch, change):
  recipients = [x.email for x in subscribers]

  subject_template = '[Perforce Autobuilder] Change @{changelist} to {watch} by {user} failed testing'
  body_template = """
  The autobuilder has discovered that testrun {testrun} has failed. This testrun was created by the
  autobuilder to verify the changes made to {watch} in @{changelist} by {user}.

  You may view the testrun at http://overtest.le.imgtec.org/viewtestrun.php?testrunid={testrun}
  """
  body_template = textwrap.dedent(body_template).strip('\n')
  msg = email.message.Message()
  msg['From'] = 'overtest@imgtec.com'
  msg['Subject'] = subject_template.format(changelist=change.changelist,
                                           watch=watch.name,
                                           user=change.username)
  msg['X-Auto-Response-Suppress'] = 'OOF' # Stop autoresponders replying
  msg.set_payload(body_template.format(testrun=testrun.id,
                                       changelist=change.changelist,
                                       watch=watch.name,
                                       user=change.username))
  msg['To'] = ', '.join(recipients)
  return recipients, msg

def _send_notification(smtp, db, testruns, recipients, msg):
  testruns = [testrun.lock(db) for testrun in testruns]
  try:
    smtp.sendmail(msg['From'], recipients, msg.as_string())
    for testrun in testruns:
      testrun.notified = True
      testrun.update(db)
    db.commit()
  except smtplib.SMTPRecipientsRefused, e:
    logger.error('Notification refused by server: %s' % e)

def send_notifications(db):
  config = BuildHostConfig.fetch_for_localhost(db)

  smtp = smtplib.SMTP()
  #smtp.set_debuglevel(1)
  smtp.connect(config.smtp_fqdn, config.smtp_port)

  for testrun in OvertestTestrun.fetch_unnotified(db):
    if testrun.passed:
      continue
    logging.info('Sending notification for testrun %d' % testrun.id)
    data = _get_notification_data(db, testrun)
    if data is None:
      continue
    watch, change, subscribers = data
    if len(subscribers) == 0:
      logger.error("No subscribers for watch named %s" % watch.name)
      continue
    recipients, msg = _make_failure_notification(db, testrun, subscribers, watch, change)
    logger.debug(msg.as_string())
    _send_notification(smtp, db, [testrun], recipients, msg)

  pass_data = []
  for testrun in OvertestTestrun.fetch_unnotified(db):
    if not testrun.passed:
      continue
    logging.info('Sending notification for testrun %d' % testrun.id)
    data = _get_notification_data(db, testrun)
    if data is None:
      continue
    watch, change, subscribers = data
    if len(subscribers) == 0:
      logger.error("No subscribers for watch named %s" % watch.name)
      continue
    pass_data.append((testrun, watch, change, subscribers))

  if pass_data:
    recipients, msg = _make_pass_notification(db, pass_data)
    logger.debug(msg.as_string())
    testruns = [testrun for testrun, _, _, _ in pass_data]
    _send_notification(smtp, db, testruns, recipients, msg)

  smtp.quit()
