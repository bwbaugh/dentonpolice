# Copyright (C) 2012--2014 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Responsible for retrieving, parsing, logging, and posting inmates."""
import datetime
import logging
import urllib
import urllib.error
import urllib.request

import http.client

from dentonpolice import inmate as inmate_module
from dentonpolice import jail
from dentonpolice import storage
from dentonpolice import twitter


log = logging.getLogger(__name__)


def main(bucket):
    """Main function

    Performs the following steps:

    1.  Scrape the Jail Custody Report.
    2.  Process to find new inmates that need to be posted.
    3.  Download mug shots.
    4.  Save a log.
    5.  Upload to Twitter.
    """
    html = jail.get_jail_report()
    if html is None:
        # Without a report, there is nothing to do.
        return
    with open('dentonpolice_recent.html', mode='w', encoding='utf-8') as f:
        # Useful for debugging to have a copy of the last seen page.
        f.write(html)
    if bucket is not None:
        # Archive the report so it can be processed or analyzed later.
        jail.save_jail_report_to_s3(
            bucket=bucket,
            html=html,
            timestamp=datetime.datetime.utcnow(),
        )
    # Parse list of inmates from webpage
    inmates = jail.parse_inmates(html)
    # Make a copy of the current parsed inmates to use later
    inmates_original = inmates[:]
    inmates = inmate_module.extract_inmates_to_process(
        inmates=inmates,
        recent_inmates=[
            inmate_module.Inmate.from_dict(data)
            for data in storage.read_log(recent=True)
        ],
    )
    # We now have our final list of inmates, so let's process them.
    if inmates:
        try:
            jail.get_mug_shots(inmates=inmates, bucket=bucket)
        except urllib.error.HTTPError as error:
            log.error(
                'HTTP %r error while getting mug shots: %r',
                error.code,
                error,
            )
            return None
        except (http.client.HTTPException, urllib.error.URLError) as error:
            log.error('Other error while getting mug shots: %r', error)
            return None
        storage.save_mug_shots(inmates)
        # Discard inmates that we couldn't save a mug shot for.
        inmates = [inmate for inmate in inmates if inmate.mug]
        # Log and post to Twitter.
        try:
            if twitter.IS_TWITTER_AVAILABLE:
                for inmate in inmates:
                    mug_shot_fname = 'mugs/{}'.format(
                        storage.most_recent_mug(inmate),
                    )
                    log.debug('Media fname: %s', mug_shot_fname)
                    with open(mug_shot_fname, mode='rb') as mug_shot_file:
                        twitter.tweet_mug_shots(
                            inmate=inmate,
                            mug_shot_file=mug_shot_file,
                        )
        finally:
            # Still want to log even if there was an uncaught error
            # while posting to Twitter.
            storage.log_inmates(inmates)
        # Remove any inmates that failed to post so they're retried.
        posted = inmates_original[:]
        for inmate in inmates:
            if not inmate.posted:
                posted = [x for x in posted if x.id != inmate.id]
        # Save the most recent list of inmates to the log for next time
        storage.log_inmates(posted, recent=True)
    # Check if there is a new record number of inmates seen on the jail report.
    (most_count, on_date) = storage.get_most_inmates_count()
    count = len(inmates_original)
    if not most_count or count > most_count:
        if twitter.IS_TWITTER_AVAILABLE:
            twitter.tweet_most_count(count, most_count, on_date)
            # Only log if we published the record.
            storage.log_most_inmates_count(count)
