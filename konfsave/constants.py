import os
import importlib.util
import logging
from pathlib import Path

if (_config_home := os.path.expandvars('$XDG_CONFIG_HOME')) != '$XDG_CONFIG_HOME':
	CONFIG_HOME = Path(_config_home)
else:
	CONFIG_HOME = Path.home() / '.config'

DATA_PATH = CONFIG_HOME / 'konfsave'
CONFIG_FILENAME = 'konfsave.ini'
DEFAULT_CONFIG_PATH = Path(__file__).parent / 'default_config.ini'
FEATURES = {
	'GIT': True
}
FEATURE_REQUIREMENTS = {
	'GIT': ('pygit2',)
}


def feature_required(feature):
	def decorator(fn):
		if FEATURES.get(feature, None):
			return fn
		description = getattr(fn, '__name__', str(fn))
		return lambda *_, **__: logging.getLogger('konfsave').error(
			f'The feature "{feature}" is required to use this functionality ({description}). '
			f'Try installing it with pip: "pip install konfsave[{feature}]"'
		)
	return decorator


for k, v in FEATURE_REQUIREMENTS.items():
	for package in v:
		if importlib.util.find_spec(package) is None:
			FEATURES[k] = False
			break
