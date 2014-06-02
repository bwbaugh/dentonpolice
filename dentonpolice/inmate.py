# Copyright (C) 2012--2014 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Code related to the representation of inmates."""
import datetime
import locale
import pprint
import re


class Inmate(object):
    """Storage class to hold name, DOB, charge, etc.

    The class __init__ will accept all keyword arguments and set them as
    class attributes. In the future it would be a good idea to switch from
    this method to actually specifying each class attribute explicitly.
    """
    def __init__(self, *args, **kwargs):
        """Inits Inmate with all keyword arguments as class attributes."""
        setattr(self, 'mug', None)
        for dictionary in args:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def get_twitter_message(self):
        """Constructs a mug shot caption """
        parts = []
        # Append arrest time
        parts.append(self.arrest)
        # Append age
        t1 = datetime.datetime.strptime(self.DOB, '%m/%d/%Y')
        t2 = datetime.datetime.strptime(self.arrest, '%m/%d/%Y %H:%M:%S')
        age = int((t2 - t1).days / 365.2425)
        parts.append(str(age) + " yrs old")
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
        cities = (r'(?:DPD|DENTON|LAKE DALLAS|FRISCO|'
                  r'DALLAS|CORINTH|RICHARDSON)*')
        extras = r'\s*(?:CO)?\s*(?:SO)?\s*(?:PD)?\s*(?:WARRANT)?(?:S)?\s*/\s*'
        for charge in self.charges:
            charge['charge'] = re.sub(r'\A' + cities + extras,
                                      '',
                                      charge['charge'])
            # pad certain characters with spaces to fix TwitPic display
            charge['charge'] = re.sub(r'([<>])', r' \1 ', charge['charge'])
            # collapse multiple spaces
            charge['charge'] = re.sub(r'\s{2,}', r' ', charge['charge'])
            parts.append(charge['charge'])
        message = '\n'.join(parts)
        # Petition link, if enough space.
        # petition = (
        #     'https://www.change.org/petitions/'
        #     'denton-police-department-make-mug-shots-available-on-request-'
        #     'instead-of-putting-all-of-them-online'
        # )
        petition = 't.co/rWrSAYThKV'
        if len(message) > 140 - 24:
            return message
        else:
            return ' '.join([message, petition])

    def __str__(self):
        """String representation of the Inmate formatted with pprint."""
        return pprint.pformat(dict((k, v) for (k, v) in vars(self).items()
                                   if k != 'mug'))

    def __repr__(self):
        """Represent the Inmate as a dictionary, not including the mug shot."""
        return str(dict((k, v) for (k, v) in vars(self).items() if k != 'mug'))
