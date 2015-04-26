# -*- coding: utf-8 -*-
"""Configuration management."""
import logging

import staticconf


log = logging.getLogger(__name__)


def load_config():
    staticconf.YamlConfiguration('config.yaml')
    staticconf.YamlConfiguration('config-env.yaml', optional=True)
