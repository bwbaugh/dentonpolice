# Copyright (C) 2012--2015 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Generally applicable utility functions."""
import logging
import signal
from hashlib import sha1


log = logging.getLogger(__name__)


class timeout(object):

    """Context manager to raise a timeout if an operation takes too long.

    Not thread safe. For more information see:
    <http://stackoverflow.com/q/2281850/1988505>
    """

    def __init__(self, seconds):
        self.seconds = seconds

    def handle_timeout(self, signum, frame):
        log.debug('Handling alarm. (threshold: %s seconds)', self.seconds)
        raise TimeoutError

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        # TODO(bwbaugh): If no error, maybe warn if time remaining is small?
        signal.alarm(0)


def git_hash(data):
    """Compute the blob style SHA1 git-hash for a given string.

    The output of this function is the same as if `git hash-object` was
    executed over a file with the same contents as `data`.

    Args:
        data: Byte string to be hashed. Unicode strings should be
            encoded (utf-8) before calling this function.

    Returns:
        String of the blob style SHA1 git-hash.

    Raises:
        TypeError if the input is a Unicode object.
    """
    # Source: http://stackoverflow.com/a/552725/1988505
    header = 'blob {size}\0'.format(size=len(data)).encode('utf-8')
    hash_object = sha1()
    hash_object.update(header)
    hash_object.update(data)
    return hash_object.hexdigest()
