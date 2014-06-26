# Copyright (C) 2012--2014 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Code related to the representation of inmates."""
import datetime
import json
import locale
import pprint
import re

from dentonpolice.zodiac import zodiac_emoji_for_date


URL_LENGTH = 23  # Assume HTTPS, otherwise HTTP is 22.
TWEET_LIMIT = 140 - URL_LENGTH  # The mug shot is included as a link.


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

    def get_twitter_message(self):
        """Constructs a mug shot caption """
        parts = []
        # Append arrest time
        parts.append(self.arrest)
        # Append first name with age
        last_name, first_name = [
            name.strip()
            for name in self.name.title().split(',', 1)
        ]
        birth_date = datetime.datetime.strptime(self.DOB, '%m/%d/%Y')
        arrest_date = datetime.datetime.strptime(
            self.arrest,
            '%m/%d/%Y %H:%M:%S',
        )
        age = int((arrest_date - birth_date).days / 365.2425)
        parts.append(
            '{first_name}, {age} yrs old {zodiac}'.format(
                first_name=first_name,
                age=age,
                zodiac=zodiac_emoji_for_date(birth_date)
            )
        )
        # Append bond (if there is data)
        if self.charges:
            bond = 0
            for charge in self.charges:
                if charge['amount']:
                    bond += int(float(charge['amount'][1:]))
            if bond:
                locale.setlocale(locale.LC_ALL, '')
                bond = locale.currency(bond, grouping=True)[:-3]
                parts.append("Bond: " + bond)
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
        for charge in self.charges:
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
            'id': self.id,
            'name': self.name,
            'seen': self.seen,
        }

    def __str__(self):
        """String representation of the Inmate formatted with pprint."""
        return pprint.pformat(dict((k, v) for (k, v) in vars(self).items()
                                   if k != 'mug'))

    def __repr__(self):
        """Represent the Inmate as a dictionary, not including the mug shot."""
        return str(dict((k, v) for (k, v) in vars(self).items() if k != 'mug'))
