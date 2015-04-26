# Copyright (C) 2012--2014 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Responsible for retrieving, parsing, logging, and posting inmates."""
import datetime
import logging
import re
import urllib
import urllib.error
import urllib.request

import http.client

from dentonpolice import jail
from dentonpolice import storage
from dentonpolice import twitter


log = logging.getLogger(__name__)


def extract_inmates_to_process(inmates):
    """Filter the inmates and return only the ones that should be posted."""
    # Load the list of inmates seen last time we got the page
    recent_inmates = storage.read_log(recent=True)
    # Find inmates that no longer appear on the page that may not be logged.
    missing = find_missing(inmates, recent_inmates)
    # Discard recent inmates with no charges listed
    recent_inmates = [recent for recent in recent_inmates if recent.charges]
    # Compare the current list with the list read last time (recent) and
    # get rid of duplicates (already logged inmates). Also discard inmates
    # that have no charges listed, or if the only charge is
    # 'LOCAL MUNICIPAL WARRANT'.
    # TODO(bwbaugh): Make this readable by converting to proper for-loopps.
    inmates = [inmate for inmate in inmates
               if inmate.charges and
               not (len(inmate.charges) == 1 and
                    re.search(r'WARRANT(?:S)?\Z', inmate.charges[0]['charge']))
               and not any((recent.id == inmate.id) and
                           (len(recent.charges) <= len(inmate.charges))
                           for recent in recent_inmates)]
    # Add to the current list those missing ones without charges that
    # also need to be logged.
    inmates.extend(missing)
    # Double check that there are no duplicates.
    # Note: this is needed due to programming logic error, but the code
    # is getting complicated so in case I don't find the bug better to check.
    for i in range(len(inmates)):
        for j in range(i + 1, len(inmates)):
            if inmates[i] and inmates[j] and inmates[i].id == inmates[j].id:
                log.warning(
                    'Removing duplicate found in inmates (ID: %s)',
                    inmates[i].id,
                )
                inmates[i] = None
    inmates = [inmate for inmate in inmates if inmate]
    return inmates


def find_missing(inmates, recent_inmates):
    """Find inmates that no longer appear on the page that may not be logged.

    Args:
        inmates: Current list of Inmates.
        recent_inmates: List of Inmates seen during the previous page
            check.

    Returns:
        A list of inmates that appear to be missing and that were
        likely not logged during previous page checks.
    """
    # Since we try not to log inmates that don't have charges listed,
    # make sure that any inmate on the recent list that doesn't appear
    # on the current page get logged even if they don't have charges.
    # Same goes for inmates without saved mug shots, as well as for
    # inmates with the only charge reason being 'LOCAL MUNICIPAL WARRANT'
    missing = []
    for recent in recent_inmates:
        potential = False
        if not recent.charges or not storage.most_recent_mug(recent):
            potential = True
        elif (len(recent.charges) == 1 and
              re.search(r'WARRANT(?:S)?\Z', recent.charges[0]['charge'])):
            potential = True
        # add if the inmate is missing from the current report or if
        # the inmate has had their charge updated.
        if potential:
            found = False
            for inmate in inmates:
                if recent.id == inmate.id:
                    found = True
                    if not recent.charges and not inmate.charges:
                        break
                    if (inmate.charges and
                        re.search(r'WARRANT(?:S)?\Z',
                                  inmate.charges[0]['charge']) is None):
                        missing.append(inmate)
                    break
            if not found:
                missing.append(recent)
                # if couldn't download the mug before and missing now,
                # go ahead and log it for future reference
                if not storage.most_recent_mug(recent):
                    storage.log_inmates([recent])
    if len(missing) > 0:
        log.info(
            'Found %s inmates without charges that are now missing',
            len(missing),
        )
    return missing


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
    inmates = extract_inmates_to_process(inmates)
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
