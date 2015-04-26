# Copyright (C) 2012--2014 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Code related to the representation of inmates."""
import hashlib
import json

from dentonpolice.util import git_hash


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
    def from_json(cls, json_string):
        """Return an instance loaded from a JSON encoded string."""
        data = json.loads(json_string)
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
