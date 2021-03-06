import os
import sys
import configparser
from pathlib import Path

import config


if (_config_home := os.path.expandvars('$XDG_CONFIG_HOME')) != '$XDG_CONFIG_HOME':
	CONFIG_HOME = Path(_config_home)
else:
	CONFIG_HOME = Path.home() / '.config'


KONFSAVE_DATA_PATH = CONFIG_HOME / 'konfsave'
KONFSAVE_CONFIG_FILENAME = 'konfsave.ini'
KONFSAVE_PROFILE_HOME = KONFSAVE_DATA_PATH / 'profiles'
KONFSAVE_PROFILE_INFO_FILENAME = '.konfsave_profile'
KONFSAVE_CURRENT_PROFILE_PATH = Path.home() / KONFSAVE_PROFILE_INFO_FILENAME
KONFSAVE_PRINT_COPYINGED_FILES = False  # Can be changed by ``config.load_config()``
KONFSAVE_DEFAULT_CONFIG_PATH = Path(__file__).parent / 'default_config.ini'
KONFSAVE_ARCHIVE_DIRECTORY = Path.home()

config.load_config()  # Circular import warning: depends on KONFSAVE_DATA_PATH, KONFSAVE_CONFIG_FILENAME, KONFSAVE_DEFAULT_CONFIG_PATH
