# -*- coding: utf-8 -*-
"""Code related to the jail report, such as retrieval and parsing."""
import datetime
import logging
import re
import urllib.request

import boto.s3.key
import http.client
import staticconf

from . import util
from .inmate import Inmate


log = logging.getLogger(__name__)

INMATE_PATTERN = re.compile(r"""
_dlInmates_lblName_\d+">(?P<name>.*?)</span>.*?
_dlInmates_lblDOB_\d+">(?P<DOB>.*?)</span>.*?
_dlInmates_Label2_\d*">(?P<arrest>.*?)</span>.*?
ImageHandler\.ashx\?imageId=(?P<id>\d+)&amp;type=thumb
""", re.DOTALL | re.X)
CHARGES_PATTERN = re.compile(r"""
_dlInmates_Charges_\d+_lblCharge_\d+">(?P<charge>.*?)</span>.*?
_dlInmates_Charges_\d+_lblBondOrFine_\d+">(?P<type>.*?)</span>.*?
_dlInmates_Charges_\d+_lblAmount_\d+">(?P<amount>.*?)</span>
""", re.DOTALL | re.X)


def _get_opener():
    """Use a proxy (Polipo through Tor) to send our requests through."""
    # If Polipo isn't running, you might need to start it manually
    #   after Tor, and if so be sure to use whatever port it is
    #   listening on (such as 8123). The default port for Polipo used
    #   in the Tor Vidalia Bundle is 8118.
    proxy_support = urllib.request.ProxyHandler({
        'http': '{host}:{port}'.format(
            host=staticconf.read('proxy.host'),
            port=staticconf.read('proxy.port'),
        )
    })
    opener = urllib.request.build_opener(proxy_support)
    return opener


def get_jail_report():
    """Retrieves the Denton City Jail Custody Report webpage."""
    log.info('Getting Jail Report')
    opener = _get_opener()
    try:
        with util.timeout(seconds=staticconf.read('timeout.open_jail_report')):
            response = opener.open('http://dpdjailview.cityofdenton.com/')
        log.debug('Reading jail report page')
        html = response.read().decode('utf-8')
    except urllib.error.HTTPError as error:
        html = None
        log.warning(
            'HTTP %r error while getting jail report: %r',
            error.code,
            error,
        )
    except (http.client.HTTPException, urllib.error.URLError) as error:
        html = None
        log.warning('Other error while getting jail report: %r', error)
    except TimeoutError:
        html = None
        log.warning('Timeout while getting jail report.')
    return html


def save_jail_report_to_s3(bucket, html, timestamp):
    """Uploads the jail report HTML to S3 with a timestamp.

    The timestamp is used to set the filename / key.

    :param html: The contents of the retrieved report.
    :type html: str
    :param timestamp: When the report was retrieved, preferably in UTC.
    :type timestamp: datetime.datetime
    """
    key = boto.s3.key.Key(
        bucket=bucket,
        name=_make_jail_report_key_name(timestamp=timestamp),
    )
    log.debug('Saving report to key: %r', key)
    key.set_contents_from_string(
        string_data=html,
        headers={
            'Content-Type': 'text/html',
        },
    )
    log.info('Saved jail report to S3: %r', key)
    return key.name


def _make_jail_report_key_name(timestamp):
    # Example: 'jail_report/dentonpolice/2015/04/21/20150421080433.html'
    return (
        'jail_report/'
        '{provenance}/'
        '{year}/'
        '{month}/'
        '{day}/'
        '{full_time}.html'
    ).format(
        provenance='dentonpolice',
        year=timestamp.strftime('%Y'),
        month=timestamp.strftime('%m'),
        day=timestamp.strftime('%d'),
        # Example: '20150421080433'
        full_time=timestamp.strftime('%Y%m%d%H%M%S'),
    )


def get_mug_shots(inmates, bucket):
    """Retrieves the mug shot for each Inmate and stores it in the Inmate."""
    log.info('Getting mug shots')
    opener = _get_opener()
    for inmate in inmates:
        log.info('Opening mug shot URL (ID: %s)', inmate.id)
        uri = (
            'http://dpdjailview.cityofdenton.com/'
            'ImageHandler.ashx?type=image&imageID={mug_id}'
        ).format(mug_id=inmate.id)
        try:
            with util.timeout(
                seconds=staticconf.read('timeout.open_one_mug_shot'),
            ):
                response = opener.open(uri)
            image_data = response.read()
        except urllib.error.HTTPError as e:
            log.warning(
                'Unable to retrieve inmate-ID %s due to HTTP %s: %r',
                inmate.id,
                e.code,
                e,
            )
            continue
        except http.client.BadStatusLine as e:
            log.warning(
                'Unable to retrieve inmate-ID %s: %r',
                inmate.id,
                e,
            )
            continue
        except TimeoutError:
            log.warning(
                'Timeout while getting mug shot for inmate-ID %s.',
                inmate.id,
            )
            continue
        inmate.mug = image_data
        if bucket is not None:
            _save_mug_shot_to_s3(bucket=bucket, inmate=inmate)


def _save_mug_shot_to_s3(bucket, inmate):
    if inmate.mug is None:
        raise ValueError('Must have image data in order to save.')
    # Compute the hash only once and save the result.
    image_hash = inmate.sha1
    key = boto.s3.key.Key(
        bucket=bucket,
        name='mugshots/{first}/{second}/{hash}.jpg'.format(
            first=image_hash[0:2],
            second=image_hash[2:4],
            hash=image_hash,
        ),
    )
    log.debug('Saving mugshot for inmate-ID %s to S3: %r', inmate.id, key)
    key.set_contents_from_string(
        string_data=inmate.mug,
        headers={
            'Cache-Control': 'max-age=31556952,public',
            'Content-Type': 'image/jpeg',
        },
        # If we've seen this before, keep the original timestamp.
        replace=False,
        policy='public-read',
    )


def parse_inmates(html):
    inmates = []
    for inmate in INMATE_PATTERN.finditer(html):
        data = inmate.groupdict()
        # Parse charges for inmate
        charges = []
        # Find end location
        next_inmate = INMATE_PATTERN.search(html, inmate.end())
        try:
            next_inmate = next_inmate.start()
        except:
            next_inmate = len(html)
        for charge in CHARGES_PATTERN.finditer(
            html,
            inmate.end(),
            next_inmate,
        ):
            charges.append(charge.groupdict())
        data['charges'] = charges
        # Store the current time as when seen
        data['seen'] = str(datetime.datetime.now())
        # Store complete Inmate object
        inmates.append(Inmate(**data))
    return inmates
