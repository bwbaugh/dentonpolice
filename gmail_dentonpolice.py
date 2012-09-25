# Copyright (C) 2012 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Adapted from:
# http://kutuma.blogspot.com/2007/08/sending-emails-via-gmail-with-python.html
"""Sends an email with an attachment via SMTP using gmail servers.

Configuration:
   gmail_user: String of the gmail acount username to use.
   gmail_pwd: String of the gmail acount password to use.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os


# Configuration

gmail_user = ''
gmail_pwd = ""
if not gmail_user or not gmail_pwd:
   raise ImportError

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587


def mail(to, subject, text, attach):
   """Send an email with attachment."""
   msg = MIMEMultipart()

   msg['From'] = gmail_user
   msg['To'] = to
   msg['Subject'] = subject

   msg.attach(MIMEText(text))

   part = MIMEBase('application', 'octet-stream')
   part.set_payload(open(attach, 'rb').read())
   encoders.encode_base64(part)
   part.add_header('Content-Disposition',
           'attachment; filename="%s"' % os.path.basename(attach))
   msg.attach(part)

   mailServer = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
   mailServer.ehlo()
   mailServer.starttls()
   mailServer.ehlo()
   mailServer.login(gmail_user, gmail_pwd)
   mailServer.sendmail(gmail_user, to, msg.as_string())
   # Should be mailServer.quit(), but that crashes...
   mailServer.close()
