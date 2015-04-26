# Copyright (C) 2012--2014 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Scrapes mug shot and inmate information from the City Jail Custody
Report page for Denton, TX and posts some of the information to Twitter
via TwitPic.

The City Jail Custody Report page that we are scraping is available here:
http://dpdjailview.cityofdenton.com/

Configuration is first required in order to post to TwitPic or Twitter.

If run as __main__, will loop and continuously check the report page.
To run only once, execute this module's main() function.
"""
import logging
import signal
import sys
import time

import boto.s3
import raven
import raven.conf
import raven.handlers.logging
import staticconf

from dentonpolice import config
from dentonpolice import report_downloader


# How often to check the City Jail Custody Report webpage
SECONDS_BETWEEN_CHECKS = 60 * 5

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
# Silence unneeded debug statements from boto.
logging.getLogger('boto').setLevel(logging.INFO)
# Don't write config values to the log. We don't use schemas yet.
logging.getLogger('staticconf.config').setLevel(logging.WARNING)

log = logging.getLogger(__name__)

config.load_config()


if staticconf.read('aws.s3.bucket', default=None):
    conn = boto.s3.connect_to_region(
        region_name=staticconf.read('aws.s3.region'),
    )
    bucket = conn.get_bucket(bucket_name=staticconf.read('aws.s3.bucket'))
    log.info('AWS configured to use bucket %r', bucket)
else:
    bucket = None

if staticconf.read('sentry.dsn', default=None):
    sentry_dsn = staticconf.read('sentry.dsn')
    log.info('Sentry logging configured.')
else:
    sentry_dsn = None
sentry_client = raven.Client(dsn=sentry_dsn)
# Send any ERROR level logs to Sentry.
sentry_handler = raven.handlers.logging.SentryHandler(sentry_client)
sentry_handler.setLevel(logging.ERROR)
raven.conf.setup_logging(sentry_handler)


def handler(signum, frame):
    log.info('Exiting due to signal-%s.', signum)
    sys.exit(0)


# Continuously checks the custody report page every SECONDS_BETWEEN_CHECKS.
log.info('Starting main loop.')
signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)
while True:
    try:
        report_downloader.main(bucket=bucket)
        log.info(
            'Sleeping for %s seconds.',
            SECONDS_BETWEEN_CHECKS,
        )
        time.sleep(SECONDS_BETWEEN_CHECKS)
    except SystemExit:
        raise
    except:
        ident = sentry_client.get_ident(sentry_client.captureException())
        log.info('Uncaught exception ident: %s', ident)
        raise
