import os
import sys
import configparser
import logging
from pathlib import Path


if (_config_home := os.path.expandvars('$XDG_CONFIG_HOME')) != '$XDG_CONFIG_HOME':
	CONFIG_HOME = Path(_config_home)
else:
	CONFIG_HOME = Path.home() / '.config'


DATA_PATH = CONFIG_HOME / 'konfsave'
CONFIG_FILENAME = 'konfsave.ini'
DEFAULT_CONFIG_PATH = Path(__file__).parent / 'default_config.ini'
