# -*- coding: utf-8 -*-
"""Code related to the jail report, such as retrieval and parsing."""
import datetime
import errno
import fnmatch
import json
import logging
import os

import staticconf


log = logging.getLogger(__name__)


def save_mug_shots(inmates):
    """Saves the mug shot image data to a file for each Inmate.

    Mug shots are saved by the Inmate's ID.
    If an image file with the same ID already exists and the new mug shot
    is different, the new mug shot is saved with the current date / time
    appended to the filename.

    Args:
        inmates: List of Inmate objects to be processed.
    """
    path = staticconf.read('path.mug_shot_dir')
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
            log.debug('Skipping inmate-ID %s with no mug shot.', inmate.id)
            continue
        # Check if there is already a mug shot for this inmate
        try:
            old_size = os.path.getsize(os.path.join(path, inmate.id + '.jpg'))
            if old_size == len(inmate.mug):
                log.debug(
                    'Skipping already saved mug shot (ID: %s)',
                    inmate.id,
                )
                continue
            else:
                for filename in os.listdir(path):
                    if (fnmatch.fnmatch(filename, '{}_*.jpg'.format(inmate.id))
                            and os.path.getsize(filename) == len(inmate.mug)):
                        log.debug(
                            'Skipping already saved of mug shot (ID: %s)',
                            inmate.id,
                        )
                        continue
                log.debug(
                    'Saving mug shot under alternate filename (ID: %s)',
                    inmate.id,
                )
                location = os.path.join(
                    path,
                    '{inmate_id}_{timestamp}.jpg'.format(
                        inmate_id=inmate.id,
                        timestamp=datetime.datetime.now().strftime(
                            '%y%m%d%H%M%S',
                        ),
                    ),
                )
        except OSError as e:
            # No such file
            if e.errno == errno.ENOENT:
                old_size = None
                location = os.path.join(
                    path,
                    '{inmate_id}.jpg'.format(inmate_id=inmate.id),
                )
            else:
                raise
        # Save the mug shot
        log.debug(
            'Writing mug shot for inmate-ID %s to: %s',
            inmate.id,
            location,
        )
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
    if recent:
        location = staticconf.read('path.recent_inmate_log')
        mode = 'w'
    else:
        location = staticconf.read('path.inmate_log')
    if recent:
        log_function = log.debug
    else:
        log_function = log.info
    with open(location, mode=mode, encoding='utf-8') as f:
        for inmate in inmates:
            log_function(
                'Recording inmate to the %s log: %s',
                'recent' if recent else 'standard',
                inmate,
            )
            f.write(inmate.to_json() + '\n')


def read_log(recent=False):
    """Loads Inmate information from log to re-create Inmate objects.

    Mug shot data is not retrieved, neither from file nor server.

    :param recent: Default of False will read from the main log file.
        Specifying True will read the separate recent log, which
        is representative of the inmates seen during the last check.
        While this is not the default, it is the option most used.
    :type recent: bool

    :returns: The raw inmate objects from the log.
    :rtype: list of dict
    """
    if recent:
        location = staticconf.read('path.recent_inmate_log')
    else:
        location = staticconf.read('path.inmate_log')
    log.debug(
        'Reading inmates from {log_name} log'.format(
            log_name='recent' if recent else 'standard',
        )
    )
    inmate_list = []
    try:
        with open(location, encoding='utf-8') as f:
            for line in f:
                inmate_list.append(json.loads(line))
    except IOError as e:
        # No such file
        if e.errno == errno.ENOENT:
            pass
        else:
            raise
    return inmate_list


def most_recent_mug(inmate):
    """Returns the filename of the most recent mug shot for the Inmate.

    Args:
        inmates: List of Inmate objects to be processed.
    """
    best = ''
    for filename in os.listdir(staticconf.read('path.mug_shot_dir')):
        # First conditional is for the original filename. The second
        # conditional is for newer timestamps.
        if (fnmatch.fnmatch(filename, '{}.jpg'.format(inmate.id)) or
                fnmatch.fnmatch(filename, '{}_*.jpg'.format(inmate.id))):
            log.debug(
                'Found recent mug candidate for inmate-ID %s: %r',
                inmate.id,
                filename,
            )
            if filename > best:
                best = filename
                log.debug(
                    'Best recent mug candidate so far for inmate-ID %s: %r',
                    inmate.id,
                    filename,
                )
    if not best:
        log.debug('Found no recent mug shot for inmate-ID %s.', inmate.id)
    return best


def get_most_inmates_count():
    """Returns the filename of the most recent mug shot for the Inmate.

    Returns:
        A tuple with the last most_count and the on_date when that occurred.
    """
    most_count, on_date = (None, None)
    try:
        with open(staticconf.read('path.most_inmate_count'), mode='r') as f:
            (most_count, on_date) = f.read().split('\n')
            most_count = int(most_count)
    except IOError as e:
        # No such file
        if e.errno == errno.ENOENT:
            log.warning('No file with statistics found.')
        else:
            raise
    except ValueError:
        log.warning('Could not parse data from file.')
    return (most_count, on_date)


def log_most_inmates_count(count):
    """Logs to file the most-count and the current date."""
    now = now = datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S')
    log.info('Logging most inmates count at %s on %s', count, now)
    with open(staticconf.read('path.most_inmate_count'), mode='w') as f:
        f.write('{}\n{}'.format(count, now))
