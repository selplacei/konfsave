import os
import sys
import configparser
from pathlib import Path


if (_config_home := os.path.expandvars('$XDG_CONFIG_HOME')) != '$XDG_CONFIG_HOME':
	CONFIG_HOME = Path(_config_home)
else:
	CONFIG_HOME = Path.home() / '.config'


KONFSAVE_DATA_PATH = CONFIG_HOME / 'konfsave'
KONFSAVE_PROFILE_HOME = KONFSAVE_DATA_PATH / 'profiles'
KONFSAVE_PROFILE_INFO_FILENAME = '.konfsave_profile'
KONFSAVE_CURRENT_PROFILE_PATH = Path.home() / KONFSAVE_PROFILE_INFO_FILENAME
KONFSAVE_PRINT_COPYINGED_FILES = False
KONFSAVE_DEFAULT_CONFIG_PATH = Path(__file__).parent / 'default_config.ini'

PATHS_TO_SAVE = set()

# Create the config file if missing
if not (KONFSAVE_DATA_PATH / 'config.ini').exists():
	print('Config file missing, copying from default')
	KONFSAVE_DATA_PATH.mkdir(parents=True, exist_ok=True)
	with open(KONFSAVE_DATA_PATH / 'config.ini', 'w') as f, open(KONFSAVE_DEFAULT_CONFIG_PATH) as d:
		f.write(d.read())

# Load the config file
with open(KONFSAVE_DATA_PATH / 'config.ini') as f:
	config = configparser.ConfigParser(allow_no_value=True)
	config.read_file(f)
	try:
		xdg_paths = list(config['XDG_CONFIG_HOME Paths To Save'].keys())
		home_paths = list(config['Home Directory Paths To Save'].keys())
	except KeyError:
		sys.stderr.write(f'Warning: malformed config file at {KONFSAVE_DATA_PATH / "config.ini"}\n')
		raise
	PATHS_TO_SAVE |= set(map(lambda p: CONFIG_HOME / p, xdg_paths))
	PATHS_TO_SAVE |= set(map(lambda p: Path.home() / p, home_paths))
