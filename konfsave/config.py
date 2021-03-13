import sys
import configparser
import itertools
import logging
import sys
from pathlib import Path
from typing import Set, Dict, List, Tuple

from . import constants

# The values referred to as "group names" include the preceding colon.

# Mapping of group names to what they contain, exactly as specified in the config
definitions: Dict[str, Set[str]] = {}
# Same as ``definitions``, but only contains metagroups (including redefined groups)
metagroups: Dict[str, Set[str]] = {}
# Mapping of group names to the paths they contain, with sub-groups recursively broken down
# Paths are absolute and resolved
paths: Dict[str, Set[Path]] = {}
# Set of files that should never be copied unless --included in the command line
exceptions = set()
# Default list of group names to save, as stored in [Defaults] -> save-list
save_list = []
profile_home: Path = None
profile_info_filename: str = None
current_profile_path: Path = None
archive_directory: Path = None


def default_paths() -> Tuple[Path]:
	"""
	Convert and return ``defaults['save-list']`` as a tuple of absolute and resolved ``Path``s.
	"""
	return tuple(itertools.chain.from_iterable(map(lambda g: paths[g], save_list)))


def load_config():
	global definitions, metagroups, paths, exceptions, save_list, profile_home
	global profile_info_filename, current_profile_path, archive_directory
	# Create the config file if missing
	if not (constants.DATA_PATH / 'konfsave.ini').exists():
		logging.getLogger('konfsave').warning('Config file missing, copying from default')
		constants.DATA_PATH.mkdir(parents=True, exist_ok=True)
		with open(constants.DATA_PATH / 'konfsave.ini', 'w') as f, open(constants.DEFAULT_CONFIG_PATH) as d:
			f.write(d.read())

	# Load the config file
	config = configparser.ConfigParser(allow_no_value=True, interpolation=_SpecialExtendedInterpolation())
	config.optionxform = str
	with open(constants.DATA_PATH / 'konfsave.ini') as f:
		config.read_file(f)
	
	# Set the logging level
	loglevel = {
		'DEBUG': logging.DEBUG,
		'INFO': logging.INFO,
		'WARNING': logging.WARNING,
		'ERROR': logging.ERROR,
		'CRITICAL': logging.CRITICAL
	}[config['Defaults']['log-level'].upper()]
	logging.basicConfig(level=loglevel)
	
	# Load exceptions
	for path in itertools.chain(
		map(
			lambda v: (Path.home() / Path(v)).resolve(),
			config['Home Directory Exceptions'].keys()
		),
		map(
			lambda v: (constants.CONFIG_HOME / Path(v)).resolve(),
			config['XDG_CONFIG_HOME Exceptions'].keys()
		)
	):
		exceptions.add(path)

	# Load path definitions
	for path, groups in itertools.chain(
		map(
			lambda v: ((Path.home() / Path(v[0])).resolve(), v[1]),
			config['Home Directory Path Definitions'].items()
		),
		map(
			lambda v: ((constants.CONFIG_HOME / Path(v[0])).resolve(), v[1]),
			config['XDG_CONFIG_HOME Path Definitions'].items()
		)
	):
		for group in groups.split(','):
			definitions.setdefault(f':{group}', set()).add(path)
	
	# Load metagroups
	for metagroup, subgroups in config['Metagroup Definitions'].items():
		if subgroups is None:
			# Redefenition of a normal group as a metagroup
			try:
				metagroups[f':{metagroup}'] = definitions[f':{metagroup}']
			except KeyError as e:
				raise ValueError(
					f'Attempted to redefine "{metagroup}" as a metagroup, but that group doesn\'t exist. '
					'Perhaps you forgot to include some files into it?'
				) from e
		else:
			# Creation of a new metagroup
			subgroups = set(map(lambda s: f':{s}', subgroups.split(',')))
			definitions[f':{metagroup}'] = subgroups
			metagroups[f':{metagroup}'] = subgroups
	
	# Recursively convert groups into paths
	undefined_groups = set()
	for group, definition in definitions.items():
		paths[group] = set()
		if isinstance(definition, Path):
			paths[group].add(definition)
			continue
		subvalues = list(definitions[group])
		while subvalues:
			subvalue = subvalues.pop()
			if isinstance(subvalue, Path):
				paths[group].add(subvalue)
			else:
				try:
					subvalues += list(definitions[subvalue])
				except KeyError:
					undefined_groups.add(subvalue)
	
	if undefined_groups:
		logging.getLogger('konfsave').info(
			f'The following groups are referenced in metagroup definitions, but are not defined: '
			+ ', '.join(sorted(undefined_groups))
		)
	
	# Load defaults
	save_list = list(map(lambda s: f':{s}', config['Defaults']['save-list'].split(',')))
	try:
		profile_home = Path(config['Defaults']['profile-home'])
		profile_info_filename = config['Defaults']['profile-info-filename']
		current_profile_path = Path(config['Defaults']['current-profile-path'])
		archive_directory = Path(config['Defaults']['archive-directory'])
	except KeyError:
		logging.getLogger('konfsave').critical(
			'Important values are missing from the config file. Did you recently update Konfsave?\n'
			'The following keys are expected in the Defaults section:\n'
			'profile-home, profile-info-filename, current-profile-path, archive-directory\n'
			f'See {str(constants.DEFAULT_CONFIG_PATH)} for example configuration,\nor simply delete '
			f'{str(constants.DATA_PATH / constants.CONFIG_FILENAME)} to reset the configuration completely.'
		)
		sys.exit(1)


class _SpecialExtendedInterpolation(configparser.ExtendedInterpolation):
	"""
	Identical to ``ExtendedInterpolation``, but also recognizes the following values:
		HOME
		CONFIG_HOME
		DATA_PATH
	which are identical to those stored in the ``constants`` module.
	"""
	def before_get(self, parser, section, option, value, defaults):
		return super().before_get(
			parser, section, option,
			value.replace(
				'${HOME}', str(Path.home())
			).replace(
				'${CONFIG_HOME}', str(constants.CONFIG_HOME)
			).replace(
				'${DATA_PATH}', str(constants.DATA_PATH)
			),
			defaults
		)
