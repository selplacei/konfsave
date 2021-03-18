import itertools
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Set, Union, TextIO, Iterable

from konfsave import config
from konfsave import constants
from konfsave import profiles

# in addition to valid identifiers
ADDITIONAL_PROFILE_NAME_CHARS = r'0123456789-+&()[]'


def validate_profile_name(name, exit_if_invalid=True) -> bool:
	valid = (''.join(
        c for c in name if c not in ADDITIONAL_PROFILE_NAME_CHARS
    )).isidentifier()
	if (not valid) and exit_if_invalid:
		profiles.logger.critical(f'The profile name "{name}" is invalid.')
		sys.exit(1)
	else:
		profiles.logger.debug(f'The profile name "{name}" is invalid.')
	return valid


def copy_allow_samefile(*args, **kwargs):
	"""
	Identical to ``shutil.copy()``, but doesn't raise an exception when copying the same file.
	"""
	try:
		shutil.copy(*args, **kwargs)
	except shutil.SameFileError:
		pass


def copy_path(source, destination, overwrite=True, follow_symlinks=False):
	profiles.logger.info(f'Copying {source}')
	destination.parent.mkdir(parents=True, exist_ok=True)
	if source.is_dir():
		shutil.copytree(
			src=source,
			dst=destination,
			symlinks=follow_symlinks,
			copy_function=copy_allow_samefile,
			dirs_exist_ok=overwrite
		)
	else:
		if overwrite or not destination.exists():
			copy_allow_samefile(source, destination, follow_symlinks=follow_symlinks)
			
			
def current_profile():
	try:
		return profile_info()['name']
	except TypeError:
		return None


def resolve_group(val) -> Set[Path]:
	"""
	Resolve a possible group, as specified in the user's config.
	If ``val`` is os.PathLike, it's converted to Path, resolved, and returned as a single item in a set.
	``val`` is considered a group if it starts with a colon.
	If the group isn't defined, KeyError is raised.
	If ``val`` doesn't either represent a path or start with a colon, ValueError is raised.
	"""
	if isinstance(val, os.PathLike):
		return {Path(val).resolve()}
	elif isinstance(val, str) and val.startswith(':'):
		return config.paths[val]  # Raises KeyError if the group is undefined
	else:
		raise ValueError(f'The value "{val}" is not a path or a group name.')


def expand_path(path) -> Set[Path]:
	"""
	If ``path`` points to a directory, return all files within the directory (recursively).
	Otherwise, return a set that contains ``path`` as its sole member.
	"""
	if path.is_dir():
		return set(path.glob('**/*'))
	return {path}


def paths_to_save(include=None, exclude=None, default_include=None) -> Set[Path]:
	"""
	Calculate and return a set of files to save to or load from a profile.
	Paths are returned as absolute and resolved,
	and point to the actual files in the home directory (never to directories).
	Directories specified in ``include``, ``exclude``, and
	``default_include`` are traversed recursively.
	
	The optional parameters ``include`` and ``exclude`` represent overrides, typically given by
	the user as command line arguments. They will always take priority over other configuration.
	The optional parameter ``default_include`` represents a list of default paths to include,
	and is typically not specified. If it is None, the list is read from the config's save-list.
	If it is an empty iterator, only values specified in ``include`` and ``exclude`` are considered.
	
	``include``, ``exclude``, and ``default_include`` must be given either as
	absolute paths (os.PathLike) or groups (starting with a colon).
	"""
	include = {*itertools.chain.from_iterable(map(resolve_group, include or ()))}
	include = {*itertools.chain.from_iterable(map(expand_path, include))}
	exclude = {*itertools.chain.from_iterable(map(resolve_group, exclude or ()))}
	exclude = {*itertools.chain.from_iterable(map(expand_path, exclude))}
	for exception in itertools.chain.from_iterable(map(expand_path, config.exceptions)):
		if exception not in include:
			exclude.add(exception)
	if default_include:
		default_include = {*itertools.chain.from_iterable(map(resolve_group, default_include))}
	else:
		default_include = {*itertools.chain.from_iterable(map(resolve_group, config.default_paths()))}
	default_include = {*itertools.chain.from_iterable(map(expand_path, default_include))}
	return (default_include | include) - exclude


_profile_info_cache = {}

def profile_info(profile_name=None, convert_values=True, use_cache=True) -> Optional[dict]:
	"""
	If the profile name is invalid, this function will print a warning and continue normally.
	
	When no argument is supplied, this will read ``config.current_profile_path``.
	The return value is ``None`` if the JSON file is missing or malformed.
	"""
	if use_cache and profile_name in _profile_info_cache:
		return _profile_info_cache[profile_name]
	if profile_name and not validate_profile_name(profile_name, exit_if_invalid=False):
		profiles.logger.warning(f'"f{profile_info}" is an invalid profile name\n')
	try:
		info = parse_profile_info(
			(config.profile_home / profile_name / config.profile_info_filename) \
				if profile_name else config.current_profile_path, convert_values=convert_values
		)
		if use_cache and info:
			_profile_info_cache[profile_name] = info
			return info.copy()
		return info
	except FileNotFoundError:
		return None


def parse_profile_info(profile_info_file: Union[TextIO, os.PathLike], convert_values=True) -> Optional[dict]:
	try:
		close_later = False
		if isinstance(profile_info_file, os.PathLike):
			f = open(profile_info_file)
			close_later = True
		else:
			f = profile_info_file
		info = json.load(f)
		if close_later:
			f.close()
		assert info['name'].isidentifier()
		info['author'] = info.get('author', None)
		info['description'] = info.get('description', None)
		info['groups'] = info.get('groups', None)
		# Currently, there are no values to convert.
		return info
	except (json.JSONDecodeError, KeyError, AssertionError) as e:
		if isinstance(profile_info_file, os.PathLike):
			profiles.logger.warning(f'Malformed profile info at {profile_info_file}\n{str(e)} \n')
		return None 
