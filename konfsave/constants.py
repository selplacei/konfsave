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
PROFILE_HOME = DATA_PATH / 'profiles'
PROFILE_INFO_FILENAME = '.konfsave_profile'
CURRENT_PROFILE_PATH = Path.home() / PROFILE_INFO_FILENAME
DEFAULT_CONFIG_PATH = Path(__file__).parent / 'default_config.ini'
ARCHIVE_DIRECTORY = Path.home()
