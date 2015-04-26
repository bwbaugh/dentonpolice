# Copyright (C) 2012--2014 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Code related to the representation of inmates."""
import hashlib
import json
import logging
import re

from dentonpolice import storage
from dentonpolice.util import git_hash


log = logging.getLogger(__name__)


class Inmate(object):

    """Storage class to hold name, DOB, charge, etc.

    Attributes:
        arrest: String of the date the inmate was arrested in the
            format: 'YYYY/MM/DD HH:MM:SS' where 'HH' is 24-hour.
        charges: List of dictionaries for each charge
            with the following attributes:
                amount: String of the USD dollar amount associated
                    with the bond or fine. For example: '$369.00'.
                charge: String of the charge description.
                type: String of the type of charge, usually either
                    'FINE', 'BOND', or 'NO BOND'.
        DOB: String of the date of birth in the format:
            'YYYY/MM/DD'.
        id: String of the integer ID from the source of the record.
        mug: String of the raw bytes of the mugshot image.
            (default None)
        name: String of the inmate's given name and surname in the
            format: 'Last, First'.
        posted: Boolean to indicate if this instance was successfully
            posted to Twitter. (default None)
        seen: String for when the record was scraped in the same
            format as `str(datetime_instance)`. For example:
            '2012-09-07 23:04:03.017000'.
        tweet: JSON serializable object representing the tweet posted,
            otherwise None if no tweet has been created since creating
            the instance.

    Properties:
        git_hash: String of the SHA1 git-hash of the `mug` attribute,
            otherwise None if the `mug` attribute is None.
        sha1: String of the standard SHA1 hash of the `mug` attribute,
            otherwise None if the `mug` attribute is None.
    """

    def __init__(self, id, name, DOB, arrest, seen, charges):
        """Create a new inmate object.

        Args:
            id: String of the integer ID from the source of the record.
            name: String of the inmate's given name and surname in the
                format: 'Last, First'.
            DOB: String of the date of birth in the format:
                'YYYY/MM/DD'.
            arrest: String of the date the inmate was arrested in the
                format: 'YYYY/MM/DD HH:MM:SS' where 'HH' is 24-hour.
            seen: String for when the record was scraped in the same
                format as `str(datetime_instance)`. For example:
                '2012-09-07 23:04:03.017000'.
            charges: List of dictionaries for each charge. See the
                class-docstring for a description of the keys.
        """
        self.arrest = arrest
        self.charges = charges
        self.DOB = DOB
        self.id = id
        self.mug = None
        self.name = name
        self.posted = None
        self.seen = seen
        self.tweet = None

    @property
    def git_hash(self):
        """The SHA1 git-hash of the `mug` attribute."""
        # TODO(bwbaugh|2014-06-28): Decide and keep only one hash.
        if self.mug is None:
            return None
        return git_hash(self.mug)

    @property
    def sha1(self):
        """The standard SHA1 hash of the `mug` attribute."""
        # TODO(bwbaugh|2014-06-28): Decide and keep only one hash.
        if self.mug is None:
            return None
        hash_object = hashlib.sha1(self.mug)
        return hash_object.hexdigest()

    @classmethod
    def from_dict(cls, data):
        """Return an instance loaded from a JSON encoded string."""
        return cls(
            data['id'],
            data['name'],
            data['DOB'],
            data['arrest'],
            data['seen'],
            data['charges'],
        )

    def to_json(self, **kwargs):
        """Return a JSON string that represents this inmate.

        NOTE: Not all attributes are included.

        Args:
            kwargs: Keyword arguments will be passed to `json.dumps`.

        Returns:
            String in JSON format. For example:

            {
              "arrest": "09/07/2012 15:30:57",
              "DOB": "11/26/1988",
              "charges": [
                {
                  "type": "BOND",
                  "charge": "DPD / FAIL TO MAINTIAN FINANCIAL RESPONSIBILITY",
                  "amount": "$569.00"
                }
              ],
              "id": "318937",
              "seen": "2012-09-07 23:04:03.017000",
              "name": "DOE, JANE"
            }
        """
        return json.dumps(self._asdict(), **kwargs)

    def _asdict(self):
        """Helper to generate a dictionary representation."""
        return {
            'arrest': self.arrest,
            'charges': self.charges,
            'DOB': self.DOB,
            'git_hash': self.git_hash,
            'id': self.id,
            'name': self.name,
            'seen': self.seen,
            'sha1': self.sha1,
            'tweet': self.tweet
        }

    def __repr__(self):
        """Represent the Inmate as a dictionary, not including the mug shot."""
        template = '{class_name}({kwargs})'
        return template.format(
            class_name=self.__class__.__name__,
            kwargs=', '.join(
                '='.join([key, repr(value)])
                for key, value in sorted(self._asdict().items())
            ),
        )


def extract_inmates_to_process(inmates, recent_inmates):
    """Filter the inmates and return only the ones that should be posted.

    :param recent_inmates: The inmates seen on the last jail report.
    :type recent_inmates: list
    """
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
