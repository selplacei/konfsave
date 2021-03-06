import sys
import configparser
import itertools
from pathlib import Path
from typing import Set, Dict, List, Tuple

from . import constants  # Circular import warning: don't interact outside of functions

# The values referred to as "group names" include the preceding colon.

# Mapping of group names to what they contain, exactly as specified in the config (including "!" paths)
definitions: Dict[str, Set[str]] = {}
# Same as ``definitions``, but only contains metagroups (including redefined groups)
metagroups: Dict[str, Set[str]] = {}
# Mapping of group names to the paths they contain, with sub-groups recursively broken down
# Paths are absolute and resolved
paths: Dict[str, Set[Path]] = {}
# Mapping of keys to values stored in the [Defaults] section, converted to applicable types
defaults = {
	'save-list': []
}


def default_paths() -> Tuple[Path]:
	"""
	Convert and return ``defaults['save-list']`` as a set of absolute and resolved ``Path``s.
	"""
	return set(*itertools.chain(map(lambda g: paths[g], defaults['save-list'])))


def load_config():
	# Create the config file if missing
	if not (constants.DATA_PATH / 'konfsave.ini').exists():
		print('Config file missing, copying from default')
		constants.DATA_PATH.mkdir(parents=True, exist_ok=True)
		with open(constants.DATA_PATH / 'konfsave.ini', 'w') as f, open(constants.DEFAULT_CONFIG_PATH) as d:
			f.write(d.read())

	# Load the config file
	config = configparser.ConfigParser(allow_no_value=True)
	config.optionxform = str
	with open(constants.DATA_PATH / 'konfsave.ini') as f:
		config.read_file(f)
	
	# Load path definitions
	for path, groups in itertools.chain(
		map(lambda v: ((Path.home() / Path(v[0])).resolve(), v[1]), config['Home Directory Path Definitions'].items()),
		map(lambda v: ((constants.CONFIG_HOME / Path(v[0])).resolve(), v[1]), config['XDG_CONFIG_HOME Path Definitions'].items())
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
				raise ValueError(f'Attempted to redefine "{metagroup}" as a metagroup, but that group doesn\'t exist.') from e
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
					
	# TODO: log this to debug (disable by default) - undefined groups are perfectly normal
	sys.stderr.write(f'Warning: the following groups are referenced in metagroup definitions, but no paths are defined for them:\n')
	sys.stderr.write(', '.join(sorted(undefined_groups)) + '\n')
	
	# Load defaults
	defaults['save-list'] = list(config['Defaults']['save-list'].split(','))
