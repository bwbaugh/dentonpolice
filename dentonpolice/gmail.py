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
    GMAIL_USER: String of the gmail acount username to use.
    GMAIL_PWD: String of the gmail acount password to use.
"""
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dentonpolice import config_dict


# Load the config values here to get a KeyError as early as possible.
SMTP_SERVER = config_dict['email']['user']
SMTP_PORT = config_dict['email']['user']
SMTP_USER = config_dict['email']['user']
SMTP_PWD = config_dict['email']['user']
if not (SMTP_SERVER and SMTP_PORT and SMTP_USER and SMTP_PWD):
    raise ImportError


def mail(to, subject, text, attach):
    """Send an email with attachment."""
    msg = MIMEMultipart()

    msg['From'] = SMTP_USER
    msg['To'] = to
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(open(attach, 'rb').read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition',
                    'attachment; filename="%s"' % os.path.basename(attach))
    msg.attach(part)

    mail_server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    mail_server.ehlo()
    mail_server.starttls()
    mail_server.ehlo()
    mail_server.login(SMTP_USER, SMTP_PWD)
    mail_server.sendmail(SMTP_USER, to, msg.as_string())
    # Should be mail_server.quit(), but that crashes...
    mail_server.close()
