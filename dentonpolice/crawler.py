# Copyright (C) 2012--2014 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Responsible for retrieving, parsing, logging, and posting inmates."""
import datetime
import io
import logging
import os
import time
import urllib
import urllib.error
import urllib.request

import http.client
import staticconf

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
    if _should_throttle(at_time=time.time()):
        return
    html = _get_jail_report(bucket=bucket)
    if html is None:
        # Without a report, there is nothing to do.
        return
    # Parse list of inmates from webpage
    inmates = jail.parse_inmates(html)
    # Get mug shots for every current inmate. (GH-12)
    try:
        jail.get_mug_shots(inmates=inmates, bucket=bucket)
    except (http.client.HTTPException, urllib.error.URLError) as error:
        log.warning('Other error while getting mug shots: %r', error)
        return
    storage.save_mug_shots(inmates)
    # Make a copy of the current parsed inmates to use later
    inmates_original = inmates[:]
    inmates = inmate_module.extract_inmates_to_process(
        inmates=inmates,
        recent_inmates=[
            inmate_module.Inmate.from_dict(data)
            for data in storage.read_log(recent=True)
        ],
    )
    _publish_new_inmates(inmates=inmates, inmates_original=inmates_original)
    _publish_record_count(inmates=inmates_original)
    _publish_updated_inmates(
        inmates=inmates,
        inmates_original=inmates_original,
    )


def _should_throttle(at_time):
    minimum_report_time = at_time - staticconf.read('minimum_report_age_s')
    try:
        last_report_time = os.path.getmtime(
            staticconf.read('path.recent_report_html'),
        )
    except OSError:
        log.warning('No recent report, so not throttling.')
        return False
    if minimum_report_time < last_report_time:
        log.info(
            (
                'Throttling since last report was generated %d s ago, '
                'which is less than %d s.'
            ),
            int(at_time - last_report_time),
            staticconf.read('minimum_report_age_s'),
        )
        return True
    return False


def _get_jail_report(bucket):
    html = jail.get_jail_report()
    if html is None:
        # Without a report, there is nothing to do.
        return None
    with open(
        staticconf.read('path.recent_report_html'),
        mode='w',
        encoding='utf-8',
    ) as f:
        # Useful for debugging to have a copy of the last seen page.
        # Also used to throttle automatic restarts.
        f.write(html)
    if bucket is not None:
        # Archive the report so it can be processed or analyzed later.
        jail.save_jail_report_to_s3(
            bucket=bucket,
            html=html,
            timestamp=datetime.datetime.utcnow(),
        )
    return html


def _publish_new_inmates(inmates, inmates_original):
    """Log and post to Twitter."""
    # Discard inmates that we couldn't save a mug shot for.
    inmates = [inmate for inmate in inmates if inmate.mug]
    if not inmates:
        return
    sorted_by_arrest = sorted(
        inmates,
        key=inmate_module.Inmate.sort_key_for_arrest,
    )
    twitter_client = twitter.get_twitter_client()
    if twitter_client is not None:
        try:
            for inmate in sorted_by_arrest:
                mug_shot_fname = 'mugs/{}'.format(
                    storage.most_recent_mug(inmate),
                )
                log.debug('Media fname: %s', mug_shot_fname)
                with open(mug_shot_fname, mode='rb') as mug_shot_file:
                    twitter.tweet_mug_shots(
                        twitter_client=twitter_client,
                        inmate=inmate,
                        caption=twitter.get_twitter_message(inmate),
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


def _publish_record_count(inmates):
    # Check if there is a new record number of inmates seen on the jail report.
    (most_count, on_date) = storage.get_most_inmates_count()
    count = len(inmates)
    log.debug(
        'Current count is %d. Most count was %d on %s',
        count,
        most_count,
        on_date,
    )
    if most_count and count <= most_count:
        return
    twitter_client = twitter.get_twitter_client()
    if twitter_client is None:
        return
    twitter.tweet_most_count(
        twitter_client=twitter_client,
        count=count,
        most_count=most_count,
        on_date=on_date,
    )
    # Only log if we published the record.
    storage.log_most_inmates_count(count)


def _publish_updated_inmates(inmates, inmates_original):
    updated_records = inmate_module.extract_updated_inmates(
        inmates=[
            inmate
            for inmate in inmates_original
            # Only consider inmates that don't look new, and only those
            #   that have a mug shot.
            if inmate not in inmates and inmate.mug
        ],
    )
    if not updated_records:
        return
    twitter_client = twitter.get_twitter_client()
    if twitter_client is None:
        return
    try:
        for record in updated_records:
            twitter.tweet_mug_shots(
                twitter_client=twitter_client,
                inmate=record['inmate'],
                caption=(
                    'Found a newer mug shot for {name}. ({arrest})'
                ).format(
                    name=record['inmate'].first_name,
                    arrest=record['inmate'].arrest,
                ),
                mug_shot_file=io.BytesIO(record['inmate'].mug),
                in_reply_to_status_id=record['last_tweet_id'],
            )
    finally:
        # Still want to log even if there was an uncaught error
        # while posting to Twitter.
        storage.log_inmates(
            inmates=[record['inmate'] for record in updated_records],
        )
