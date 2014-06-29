# Copyright (C) 2012--2014 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Generally applicable utility functions."""
from hashlib import sha1


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
