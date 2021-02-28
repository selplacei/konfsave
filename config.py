import os
from pathlib import Path


if (_config_home := os.path.expandvars('$XDG_CONFIG_HOME')) != '$XDG_CONFIG_HOME':
	KONFSAVE_DATA_PATH = Path(_config_home) / 'konfsave'
else:
	KONFSAVE_DATA_PATH = Path.home() / '.config' / 'konfsave'

KONFSAVE_CURRENT_PROFILE_PATH = KONFSAVE_DATA_PATH / 'current_profile'

PATHS_TO_SAVE = {  # These paths are relative to the home directory.
	
}
