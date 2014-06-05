# Copyright (C) 2012--2014 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
"""Utilities for zodiac sign calculations.

Adapted from a Stack Overflow question about calculating zodiac signs:
http://stackoverflow.com/q/3274597/1988505
"""
from bisect import bisect
from collections import namedtuple


DateSignPair = namedtuple('DateSignPair', 'month day sign')


_DATE_TO_SIGN_HELPER = [
    DateSignPair(month=1, day=20, sign='capricorn'),
    DateSignPair(month=2, day=18, sign='aquarius'),
    DateSignPair(month=3, day=20, sign='pisces'),
    DateSignPair(month=4, day=20, sign='aries'),
    DateSignPair(month=5, day=21, sign='taurus'),
    DateSignPair(month=6, day=21, sign='gemini'),
    DateSignPair(month=7, day=22, sign='cancer'),
    DateSignPair(month=8, day=23, sign='leo'),
    DateSignPair(month=9, day=23, sign='virgo'),
    DateSignPair(month=10, day=23, sign='libra'),
    DateSignPair(month=11, day=22, sign='scorpius'),
    DateSignPair(month=12, day=22, sign='sagittarius'),
    DateSignPair(month=12, day=31, sign='capricorn'),
]

_SIGN_TO_EMOJI_HELPER = {
    # Found the Unicode from: http://apps.timwhitlock.info/emoji/tables/unicode
    'aries': '\u2648',
    'taurus': '\u2649',
    'gemini': '\u264A',
    'cancer': '\u264B',
    'leo': '\u264C',
    'virgo': '\u264D',
    'libra': '\u264E',
    'scorpius': '\u264F',
    'sagittarius': '\u2650',
    'capricorn': '\u2651',
    'aquarius': '\u2652',
    'pisces': '\u2653',
}


def zodiac_emoji_for_date(date):
    """Get the emoji unicode character for the zodiac of a date or datetime."""
    index = bisect(
        _DATE_TO_SIGN_HELPER,
        (date.month, date.day),
    )
    sign = _DATE_TO_SIGN_HELPER[index].sign
    emoji = _SIGN_TO_EMOJI_HELPER[sign]
    return emoji
