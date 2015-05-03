# -*- coding: utf-8 -*-
"""Code related to the jail report, such as retrieval and parsing."""
import datetime
import locale
import logging
import re

import staticconf
from twython import Twython

from dentonpolice import zodiac


log = logging.getLogger(__name__)

URL_LENGTH = 23  # Assume HTTPS, otherwise HTTP is 22.
TWEET_LIMIT = 140 - URL_LENGTH  # The mug shot is included as a link.


def get_twitter_client():
    if not staticconf.read_bool('twitter.enabled', default=False):
        return None
    return Twython(
        app_key=staticconf.read('twitter.api_key'),
        app_secret=staticconf.read('twitter.api_secret'),
        oauth_token=staticconf.read('twitter.access_token'),
        oauth_token_secret=staticconf.read('twitter.access_token_secret'),
    )


def tweet_mug_shots(
        twitter_client, inmate, caption, mug_shot_file, **tweet_params):
    """Posts to Twitter each inmate using their mug shot and caption.

    Args:
        inmates: List of Inmate objects to be processed.
    """
    if twitter_client is None:
        log.info('Not posting mug shot since Twitter is disabled.')
        return
    log.info('Posting to Twitter (ID: %s)', inmate.id)
    log.debug('Status: {status!r}'.format(status=caption))
    try:
        inmate.tweet = twitter_client.update_status_with_media(
            status=caption,
            media=mug_shot_file,
            **tweet_params
        )
    except Exception as error:
        inmate.posted = False
        log.warning(
            'Exception while trying to tweet ID-%s: %r',
            inmate.id,
            error,
        )
        # TODO(bwbaugh|2014-06-01): Change to handle known types of
        # exceptions without having to re-raise.
        if str(error).endswith('Status is a duplicate.'):
            # Should only happen when recovering the script after
            # fixing / handling an error.
            log.warn('Status is a duplicate. Suppressing error')
            inmate.posted = True
        else:
            raise
    else:
        inmate.posted = True


def get_twitter_message(inmate):
    """Constructs a mug shot caption """
    parts = []
    # Append arrest time
    parts.append(inmate.arrest)
    # Append first name with age
    last_name, first_name = [
        name.strip()
        for name in inmate.name.title().split(',', 1)
    ]
    birth_date = datetime.datetime.strptime(inmate.DOB, '%m/%d/%Y')
    arrest_date = datetime.datetime.strptime(
        inmate.arrest,
        '%m/%d/%Y %H:%M:%S',
    )
    age = int((arrest_date - birth_date).days / 365.2425)
    parts.append(
        '{first_name}, {age} yrs old {zodiac}'.format(
            first_name=first_name,
            age=age,
            zodiac=zodiac.zodiac_emoji_for_date(birth_date)
        )
    )
    # Append bond (if there is data)
    if inmate.charges:
        bond = 0
        for charge in inmate.charges:
            if charge['amount']:
                bond += int(float(charge['amount'][1:]))
        if bond:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            bond = locale.currency(bond, grouping=True)[:-3]
            parts.append('Bond: ' + bond)
    # Append list of charges
    # But first shorten the charge text
    city_list = [
        'ARLINGTON',
        'CORINTH',
        'DALLAS',
        'DC',
        'DECATUR',
        'DENTON',
        'DPD',
        'EULESS',
        'FLOWER MOUND',
        'FRISCO',
        'LAKE DALLAS',
        'LEWISVILLE',
        'RICHARDSON',
        'TARRANT',
        'TDCJ',
    ]
    cities = '(?:{cities})*'.format(cities='|'.join(city_list))
    extras = r'\s*(?:CO)?\s*(?:SO)?\s*(?:PD)?\s*(?:WARRANT)?(?:S)?\s*/\s*'
    for charge in inmate.charges:
        charge['charge'] = re.sub(r'\A' + cities + extras,
                                  '',
                                  charge['charge'])
        # pad certain characters with spaces to fix TwitPic display
        charge['charge'] = re.sub(r'([<>])', r' \1 ', charge['charge'])
        # collapse multiple spaces
        charge['charge'] = re.sub(r'\s{2,}', r' ', charge['charge'])
        if charge['charge']:
            parts.append(charge['charge'])
    message = '\n'.join(parts)
    # Truncate to TWEET_LIMIT, otherwise we will get HTTP 403 when
    # submitting to Twitter for the status being over 140 chars.
    # TODO(bwbaugh|2014-06-01): Truncate outside of this method, or
    # make it a kwarg option.
    message = message[:TWEET_LIMIT]
    # Petition link, if enough space.
    # petition = (
    #     'https://www.change.org/petitions/'
    #     'denton-police-department-make-mug-shots-available-on-request-'
    #     'instead-of-putting-all-of-them-online'
    # )
    petition = 't.co/rWrSAYThKV'
    # Check that there is room for the URI. PLus one for '\n'.
    if len(message) > TWEET_LIMIT - (URL_LENGTH + 1):
        return message
    else:
        message_with_petition = '\n'.join([message, petition])
        if len(message_with_petition) > 140:
            # TODO(bwbaugh|2014-06-01): Remove sanity check after
            # comfortable with results. Really need unit tests. :(
            raise AssertionError(
                message, len(message), petition, len(petition),
            )
        return message_with_petition


def tweet_most_count(twitter_client, count, most_count, on_date):
    """Tweet that we have seen the most number of inmates in jail at once."""
    if twitter_client is None:
        log.info('Not posting most-count since Twitter is disabled.')
    log.info('Posting new record of %s inmates', count)
    # Post to twitter and log
    now = datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S')
    message = (
        'New Record: {count} inmates listed in jail as of {time}.'.format(
            count=count,
            time=now,
        )
    )
    if most_count and on_date:
        message += ' Last record was {count} inmates on {date}'.format(
            count=most_count,
            date=on_date,
        )
    # TODO(bwbaugh|2014-06-01): Twitter will auto shorten the URL, so
    # we might be able to use a smaller length here.
    jail_url = 'http://dpdjailview.cityofdenton.com/'
    if len(message) + len(jail_url) + 1 <= 140:
        message += ' ' + jail_url.decode('utf-8')
    twitter_client.update_status(status=message)
