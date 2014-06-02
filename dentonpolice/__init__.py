# Copyright (C) 2012 Brian Wesley Baugh
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# To view a copy of this license, visit:
# http://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Adapted from:
# http://kutuma.blogspot.com/2007/08/sending-emails-via-gmail-with-python.html
"""Scraper that retrieves and posts mug shot data.

Attributes:
    config_dict: Dictionary with any configuration that was found,
        otherwise it is populated with default values.
"""
import yaml


# Start with defaults in case the user doesn't provide any.
config_dict = {
    'email': {
        'server': '',
        'port': 587,
        'user': '',
        'password': '',
    },
    'proxy': {
        'host': '127.0.0.1',
        'port': 8123,
    },
    'twitpic email address': '',
    'twitter': {
        'API key': '',
        'API secret': '',
        'Access token': '',
        'Access token secret': '',
    },
}
try:
    with open('config.yaml') as config_file:
        config_dict.update(yaml.load(config_file))
except FileNotFoundError:
    pass
else:
    del config_file
