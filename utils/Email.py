"""
A simple Email module to send emails to a user.
"""
import smtplib
import types
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Mailer:
  """
  This is a simple wrapper that combines functionality from the
  smtplib and email modules.
  """
  smtpd = None

  def __init__(self, hostname, port, postmaster=None):
    """
    Connect to the hostname at port.

    If the email failed to send then an email containing the reason
    for failure is mailed to the 'postmaster'.
    """
    self.smtpd = smtplib.SMTP()
    self.smtpd.connect(hostname, port)

    self.postmaster = postmaster

  def __del__(self):
    """
    Close any open connections to smtp servers.
    """
    self.smtpd.quit()

  def send(self, from_addr, to_addr, msg):
    """
    Send an email message, 'msg', from 'from_addr' to 'to_addr'.

    Return a boolean value indicating whether the email was sent
    successfully.
    """
    # Ensure the 'to' addresses are in a list
    if type(to_addr) != types.ListType:
      to_addr = [to_addr]

    rejected_recipients = ""
    all_rejected_recipients = ""
    try:
      rejected_recipients = self.smtpd.sendmail(from_addr, to_addr, msg)
    except smtplib.SMTPRecipientsRefused:
      # All recipients were rejected.
      all_reject_recipients = to_addr
      return False

    # 'rejected_recipients' contains a list of usernames that the smtp
    # server says are invalid.
    if rejected_recipients:
      msg = "X-Auto-Response-Suppress: OOF\n"
      msg += "To: %s\n" % self.postmaster
      msg += "From: overtest@imgtec.com\n"
      msg += "Subject: Email Failure\n\n"
      msg += "Failed to send email to the following recipients:\n"

      if all_rejected_recipients:
        for r in all_reject_recipients:
          msg += "%s\n" % r
      else:
        for r in rejected_recipients.keys():
          msg += "%s:%s\n" % (r, rejected_recipients[r][1])

      # Don't try to recover from this if it fails, there's nothing
      # we can do.
      try:
        self.smtpd.sendmail(from_addr, postmaster, msg)
      except:
        pass

    return True

  def sendHtmlEmail (self, from_addr, to_addr, subject, html, text):
    """
    Create an HTML multipart message
    """
    # Ensure the 'to' addresses are in a list
    if type(to_addr) != types.ListType:
      to_addr = [to_addr]

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')

    msg['X-Auto-Response-Suppress'] = "OOF"
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr[0]
    if len(to_addr) > 1:
      msg['Cc'] = "; ".join(to_addr[1:])
    
    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    return self.send(from_addr, to_addr, msg.as_string())

