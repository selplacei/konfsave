import configparser
from pathlib import Path

import constants  # Circular import warning: don't interact outside of functions

# The values referred to as "group names" include the preceding colon.
definitions = {}  # Mapping of group names to what they contain, as specified in the config
metagroups = {}  # Same as ``definitions``, but only contains metagroups (including redefined groups)
paths = {}  # Mapping of group names to the paths they contain, with sub-groups recursively broken down
			# Paths are stored as Path objects, absolute, and resolved
defaults = {  # Mapping of keys to values stored in the [Defaults] section, converted to applicable types
	'default-groups': []
}


def load_config():
	# Create the config file if missing
	if not (constants.KONFSAVE_DATA_PATH / 'konfsave.ini').exists():
		print('Config file missing, copying from default')
		constants.KONFSAVE_DATA_PATH.mkdir(parents=True, exist_ok=True)
		with open(KONFSAVE_DATA_PATH / 'konfsave.ini', 'w') as f, open(constants.KONFSAVE_DEFAULT_CONFIG_PATH) as d:
			f.write(d.read())

	# Load the config file
	config = configparser.ConfigParser(allow_no_value=True)
	config.optionxform = str
	with open(constants.KONFSAVE_DATA_PATH / 'konfsave.ini') as f:
		config.read_file(f)
