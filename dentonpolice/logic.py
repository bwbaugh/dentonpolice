# Copyright (C) 2012--2014 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Responsible for retrieving, parsing, logging, and posting inmates."""
import ast
import datetime
import errno
import fnmatch
import http.client
import logging
import os
import re
import smtplib
import socket
import urllib
import urllib.error
import urllib.request

try:
    from twython3k import Twython
except ImportError:
    print('Unable to load Twitter library. Disabling Twitter features.',
          file=sys.stderr)
    Twython = None

from dentonpolice.inmate import Inmate
try:
    from dentonpolice.gmail import mail
except ImportError:
    print('Unable to load gmail library. Disabling submitting to TwitPic.',
          file=sys.stderr)
    mail = None


# TwitPic image upload email address.
# Used to post mug shot and accompanying caption to TwitPic.
TWITPIC_EMAIL_ADDRESS = ''

# Twitter account info.
# Used to post most number of inmates in jail at once information.
TWITTER_TOKEN = ''
TWITTER_SECRET = ''
OAUTH_TOKEN = ''
OAUTH_TOKEN_SECRET = ''

# Proxy setup
# If Polipo isn't running, you might need to start it manually after Tor,
# and if so be sure to use whatever port it is listening on (such as 8123).
# The default port for Polipo used in the Tor Vidalia Bundle is 8118.
PROXY_PORT = 8123
# Use a proxy; in this case set to use Polipo (through Tor)
proxy_support = urllib.request.ProxyHandler({'http':
                                             '127.0.0.1:'
                                             '{}'.format(PROXY_PORT)})
opener = urllib.request.build_opener(proxy_support)
opener.addheaders = [('User-agent', 'Mozilla/5.0')]


def get_jail_report():
    """Retrieves the Denton City Jail Custody Report webpage."""
    logger = logging.getLogger('JailReport')
    logger.debug("Getting Jail Report")
    # Uncomment to read from file instead of LIVE web page
##    with open('dentonpolice_recent.html') as f:
##        return f.read()
    logger.debug("Opening URL")
    response = opener.open('http://dpdjailview.cityofdenton.com/')
    logger.debug("Reading page")
    html = response.read().decode('utf-8')
    with open('dentonpolice_recent.html', mode='w', encoding='utf-8') as f:
        f.write(html)
    return html


def get_mug_shots(inmates):
    """Retrieves the mug shot for each Inmate and stores it in the Inmate."""
    logger = logging.getLogger('get_mug_shots')
    logger.debug("Getting mug shots")
    for inmate in inmates:
        try:
            logger.debug("Opening mug shot URL (ID: {})".format(inmate.id))
            response = opener.open("http://dpdjailview.cityofdenton.com/"
                                   "ImageHandler.ashx?type=image&imageID=" + inmate.id)
            inmate.mug = response.read()
        except urllib.error.HTTPError as e:
            if e.code == 500:
                logger.warning('Unable to retrieve: Internal Server Error '
                               '(ID: %s)', inmate.id)
                inmate.mug = None


def save_mug_shots(inmates):
    """Saves the mug shot image data to a file for each Inmate.

    Mug shots are saved by the Inmate's ID.
    If an image file with the same ID already exists and the new mug shot
    is different, the new mug shot is saved with the current date / time
    appended to the filename.

    Args:
        inmates: List of Inmate objects to be processed.
    """
    logger = logging.getLogger('save_mug_shots')
    path = "mugs/"
    # Make mugs/ folder
    try:
        os.makedirs(path)
    except OSError as e:
        # File/Directory already exists
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    # Save each inmate's mug shot
    for inmate in inmates:
        # Skip inmates with no mug shot
        if inmate.mug is None:
            continue
        # Check if there is already a mug shot for this inmate
        try:
            old_size = os.path.getsize(path + inmate.id + '.jpg')
            if old_size == len(inmate.mug):
                logger.debug("Skipping save of mug shot (ID: %s)", inmate.id)
                continue
            else:
                for filename in os.listdir(path):
                    if (fnmatch.fnmatch(filename, '{}_*.jpg'.format(inmate.id))
                            and os.path.getsize(filename) == len(inmate.mug)):
                        logger.debug("Skipping save of mug shot (ID: %s)",
                                     inmate.id)
                        continue
                logger.debug("Saving mug shot under alternate filename "
                             "(ID: {})".format(inmate.id))
                location = (path + inmate.id + '_' +
                            datetime.datetime.now().strftime("%y%m%d%H%M%S") +
                            '.jpg')
        except OSError as e:
            # No such file
            if e.errno == errno.ENOENT:
                old_size = None
                location = path + inmate.id + '.jpg'
            else:
                raise
        # Save the mug shot
        with open(location, mode='wb') as f:
            f.write(inmate.mug)


def log_inmates(inmates, recent=False, mode='a'):
    """Log to file all Inmate information excluding mug shot image data.

    Args:
        inmates: List of Inmate objects to be processed.
        recent: Default of False will append to the main log file.
            Specifying True will overwrite the separate recent log, which
            is representative of the inmates seen during the last check.
    """
    logger = logging.getLogger('log_inmates')
    if recent:
        location = 'dentonpolice_recent.txt'
        mode = 'w'
    else:
        location = 'dentonpolice_log.txt'
    logger.debug("Saving inmates to {} log".format("recent" if recent
                                                   else "standard"))
    with open(location, mode=mode, encoding='utf-8') as f:
        for inmate in inmates:
            if not recent:
                logger.info("Recording Inmate:\n%s", inmate)
            f.write(repr(inmate) + '\n')


def read_log(recent=False):
    """Loads Inmate information from log to re-create Inmate objects.

    Mug shot data is not retrieved, neither from file nor server.

    Args:
        recent: Default of False will read from the main log file.
            Specifying True will read the separate recent log, which
            is representative of the inmates seen during the last check.
            While this is not the default, it is the option most used.
    """
    logger = logging.getLogger('read_log')
    if recent:
        location = 'dentonpolice_recent.txt'
    else:
        location = 'dentonpolice_log.txt'
    logger.debug("Reading inmates from {} log".format("recent" if recent else
                                                      "standard"))
    inmates = []
    try:
        with open(location, encoding='utf-8') as f:
            for line in f:
                inmates.append(Inmate(ast.literal_eval(line)))
    except IOError as e:
        # No such file
        if e.errno == errno.ENOENT:
            pass
        else:
            raise
    return inmates


def most_recent_mug(inmate):
    """Returns the filename of the most recent mug shot for the Inmate.

    Args:
        inmates: List of Inmate objects to be processed.
    """
    best = ''
    for filename in os.listdir('mugs/'):
        if fnmatch.fnmatch(filename, '{}*.jpg'.format(inmate.id)):
            if filename > best:
                best = filename
    return best


def post_twitpic(inmates):
    """Posts to TwitPic each inmate using their mug shot and caption.

    Args:
        inmates: List of Inmate objects to be processed.
    """
    logger = logging.getLogger('post_twitpic')
    for inmate in inmates:
        message = inmate.get_twitter_message()
        logger.info('Posting to TwitPic (ID: %s)', inmate.id)
        try:
            mail(to=TWITPIC_EMAIL_ADDRESS,
                 subject=message,  # Caption
                 text=repr(inmate),  # Serves as a log that can later be loaded.
                 attach="mugs/{}".format(most_recent_mug(inmate)))
        except smtplib.SMTPDataError:
            inmate.posted = False
            logger.warning('SMTPDataError for {id}'.format(id=inmate.id))
        else:
            inmate.posted = True


def get_most_inmates_count():
    """Returns the filename of the most recent mug shot for the Inmate.

    Returns:
        A tuple with the last most_count and the on_date when that occurred.
    """
    logger = logging.getLogger('get_most_inmates_count')
    most_count, on_date = (None, None)
    try:
        with open('dentonpolice_most.txt', mode='r') as f:
            (most_count, on_date) = f.read().split('\n')
            most_count = int(most_count)
    except IOError as e:
        # No such file
        if e.errno == errno.ENOENT:
            logger.warning('No file with statistics found.')
        else:
            raise
    except ValueError:
        logger.warning('Could not parse data from file.')
    return (most_count, on_date)


def log_most_inmates_count(count):
    """Logs to file the most-count and the current date."""
    logger = logging.getLogger('log_most_inmates_count')
    now = now = datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S')
    logger.info('Logging most inmates count at %s on %s', count, now)
    with open('dentonpolice_most.txt', mode='w') as f:
        f.write('{}\n{}'.format(count, now))


def parse_inmates(html):
    inmate_pattern = re.compile(r"""
    _dlInmates_lblName_\d+">(?P<name>.*?)</span>.*?
    _dlInmates_lblDOB_\d+">(?P<DOB>.*?)</span>.*?
    _dlInmates_Label2_\d*">(?P<arrest>.*?)</span>.*?
    ImageHandler\.ashx\?imageId=(?P<id>\d+)&amp;type=thumb
    """, re.DOTALL | re.X)
    charges_pattern = re.compile(r"""
    _dlInmates_Charges_\d+_lblCharge_\d+">(?P<charge>.*?)</span>.*?
    _dlInmates_Charges_\d+_lblBondOrFine_\d+">(?P<type>.*?)</span>.*?
    _dlInmates_Charges_\d+_lblAmount_\d+">(?P<amount>.*?)</span>
    """, re.DOTALL | re.X)
    inmates = []
    for inmate in inmate_pattern.finditer(html):
        data = inmate.groupdict()
        # Parse charges for inmate
        charges = []
        # Find end location
        next_inmate = inmate_pattern.search(html, inmate.end())
        try:
            next_inmate = next_inmate.start()
        except:
            next_inmate = len(html)
        for charge in charges_pattern.finditer(html, inmate.end(),
                                               next_inmate):
            charges.append(charge.groupdict())
        data['charges'] = charges
        # Store the current time as when seen
        data['seen'] = str(datetime.datetime.now())
        # Store complete Inmate object
        inmates.append(Inmate(data))
    return inmates


def find_missing(inmates, recent_inmates):
    """Find inmates that no longer appear on the page that may not be logged.

    Args:
        inmates: Current list of Inmates.
        recent_inmates: List of Inmates seen during the previous page check.

    Returns:
        A list of inmates that appear to be missing and that were likely
        not logged during previous page checks.
    """
    logger = logging.getLogger('find_missing')
    # Since we try not to log inmates that don't have charges listed,
    # make sure that any inmate on the recent list that doesn't appear
    # on the current page get logged even if they don't have charges.
    # Same goes for inmates without saved mug shots, as well as for
    # inmates with the only charge reason being 'LOCAL MUNICIPAL WARRANT'
    missing = []
    for recent in recent_inmates:
        potential = False
        if not recent.charges or not most_recent_mug(recent):
            potential = True
        elif (len(recent.charges) == 1 and
              re.search(r'WARRANT(?:S)?\Z', recent.charges[0]['charge'])):
            potential = True
        # add if the inmate is missing from the current report or if the
        # inmate has had their charge updated
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
                if not most_recent_mug(recent):
                    log_inmates([recent])
    if len(missing) > 0:
        logger.info("Found %s inmates without charges that are now missing",
                    len(missing))
    return missing


def tweet_most_count(count, most_count, on_date):
    """Tweet that we have seen the most number of inmates in jail at once."""
    logger = logging.getLogger('tweet_most_count')
    logger.info('Posting new record of %s inmates', count)
    # Post to twitter and log
    jail_url = Twython.shortenURL('http://dpdjailview.cityofdenton.com/')
    now = datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S')
    message = ('New Record: {} inmates listed in jail '
               'as of {}.').format(count, now)
    if most_count and on_date:
        message += ' Last record was {} inmates on {}'.format(most_count,
                                                              on_date)
    if len(message) + len(jail_url) + 1 <= 140:
        message += ' ' + jail_url.decode('utf-8')
    twitter = Twython(twitter_token=TWITTER_TOKEN,
                      twitter_secret=TWITTER_SECRET,
                      oauth_token=OAUTH_TOKEN,
                      oauth_token_secret=OAUTH_TOKEN_SECRET)
    twitter.updateStatus(status=message)
    log_most_inmates_count(count)


def main():
    """Main function

    Used to scrape the Jail Custody Report, download mug shots, save a log,
    and upload to Twitter.
    """
    logger = logging.getLogger('main')
    # Get the Jail Report webpage
    try:
        html = get_jail_report()
    except urllib.error.HTTPError as e:
        # Service Unavailable
        if e.code == 503:
            reason = "HTTP Error 503: Service Unavailable"
        else:
            reason = e
        logger.error("JailReport: %r", reason)
        return
    except http.client.HTTPException as e:
        logger.error("JailReport: %r", e)
        return
    except urllib.error.URLError as e:
        logger.error("JailReport: %r", e)
        return
    # Parse list of inmates from webpage
    inmates = parse_inmates(html)
    # Load the list of inmates seen last time we got the page
    recent_inmates = read_log(recent=True)
    # Find inmates that no longer appear on the page that may not be logged.
    missing = find_missing(inmates, recent_inmates)
    # Make a copy of the current parsed inmates to use later
    inmates_original = inmates[:]
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
                logger.warning('Removing duplicate found in inmates (ID: %s)',
                               inmates[i].id)
                inmates[i] = None
    inmates = [inmate for inmate in inmates if inmate]
    # We now have our final list of inmates, so let's process them.
    if inmates:
        try:
            get_mug_shots(inmates)
        except urllib.error.HTTPError as e:
            # Service Unavailable
            if e.code == 503:
                reason = "HTTP Error 503: Service Unavailable"
            else:
                reason = e
            logger.warning("get_mug_shots: %r", reason)
            return
        except http.client.HTTPException as e:
            logger.warning("get_mug_shots: %r", e)
            return
        save_mug_shots(inmates)
        # Discard inmates that we couldn't save a mug shot for.
        inmates = [inmate for inmate in inmates if inmate.mug]
        # Log and post to TwitPic
        log_inmates(inmates)
        if TWITPIC_EMAIL_ADDRESS and mail is not None:
            try:
                post_twitpic(inmates)
            except socket.gaierror:
                logger.warning("post_twitpic: socket.gaierror")
                return
        # Remove any inmates that failed to post so they're retried.
        posted = inmates_original[:]
        for inmate in inmates:
            if not inmate.posted:
                posted = [x for x in posted if x.id != inmate.id]
        # Save the most recent list of inmates to the log for next time
        log_inmates(posted, recent=True)
    # Check if there is a new record number of inmates seen on the jail report.
    (most_count, on_date) = get_most_inmates_count()
    count = len(inmates_original)
    if not most_count or count > most_count:
        if (Twython is not None and
                TWITTER_TOKEN and TWITTER_SECRET and
                OAUTH_TOKEN and OAUTH_TOKEN_SECRET):
            tweet_most_count(count, most_count, on_date)
