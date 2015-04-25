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
import time

import boto.s3
import raven
import raven.conf
import raven.handlers.logging

from dentonpolice import config_dict
from dentonpolice.logic import main


# How often to check the City Jail Custody Report webpage
SECONDS_BETWEEN_CHECKS = 60 * 5


# Logging level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

log = logging.getLogger(__name__)

if 'aws' in config_dict:
    conn = boto.s3.connect_to_region(
        region_name=config_dict['aws']['s3']['region'],
    )
    bucket = conn.get_bucket(bucket_name=config_dict['aws']['s3']['bucket'])
    log.info('AWS configured to use bucket %r', bucket)
else:
    bucket = None

if 'sentry' in config_dict:
    sentry_dsn = config_dict['sentry']['dsn']
    log.info('Sentry logging configured.')
else:
    sentry_dsn = None
sentry_client = raven.Client(dsn=sentry_dsn)
# Send any ERROR level logs to Sentry.
sentry_handler = raven.handlers.logging.SentryHandler(sentry_client)
raven.conf.setup_logging(sentry_handler)

# Continuously checks the custody report page every SECONDS_BETWEEN_CHECKS.
logging.info("Starting main loop.")
while True:
    try:
        main(bucket=bucket)
        log.info(
            'Sleeping for %s seconds.',
            SECONDS_BETWEEN_CHECKS,
        )
        time.sleep(SECONDS_BETWEEN_CHECKS)
    except KeyboardInterrupt:
        log.info('Exiting due to SIGINT.')
        break
    except:
        ident = sentry_client.get_ident(sentry_client.captureException())
        log.info('Uncaught exception ident: %s', ident)
        raise
