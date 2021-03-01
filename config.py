import os
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

_XDG_CONFIG_PATHS_TO_SAVE = {
	# These paths are relative to $XDG_CONFIG_HOME (usually ~/.config).
	# The actual files must be within the home directory, i.e. no '..'s that go outside.
	'gtk-2.0',
	'gtk-3.0',
	'Kvantum',
	
	'konfsave/config.py',
	'dolphinrc',
	'konsolerc',
	'kcminputrc',
	'kdeglobals',
	'kglobalshortcutsrc',
	'klipperrc',
	'krunnerrc',
	'kscreenlockerrc',
	'ksmserverrc',
	'kwinrc',
	'kwinrulesrc',
	'plasma-org.kde.plasma.desktop-appletsrc',
	'plasmarc',
	'plasmashellrc',
	'gtkrc',
	'gtkrc-2.0'
}

PATHS_TO_SAVE = set(map(lambda p: Path.home() / p, {
	# These paths are relative to the home directory.
	# The actual files must be within the home directory, i.e. no '..'s that go outside.
	'.kde4'
})) | set(map(lambda p: CONFIG_HOME / p, _XDG_CONFIG_PATHS_TO_SAVE))
