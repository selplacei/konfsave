import sys
import os
import itertools
import shutil
import json
from pathlib import Path
from typing import Optional, Set, Union, TextIO

from . import constants
from . import config
# TODO: write proper docstrings so that this can be used as a library

def validate_profile_name(name, exit_if_invalid=True) -> bool:
	valid = name.isidentifier()
	if (not valid) and exit_if_invalid:
		sys.stderr.write(f'The profile name "{name}" is invalid.\n')
		sys.exit(1)
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
	if config.print_copyinged_files:
		print(f'Copying {path}')
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
	Paths are returned as absolute and resolved, and point to the actual files in the home directory (never directories).
	
	The optional parameters ``include`` and ``exclude`` represent overrides, typically given by the user as
	command line arguments. They will always take priority over other configuration.
	The optional parameter ``default_include`` represents a list of default paths to include, and is typically not specified.
	If it is None, the list is read from the config's save-list.
	If it is an empty iterator, only values specified in ``include`` and ``exclude`` are considered.
	
	``include``, ``exclude``, and ``default_include`` must be given either as absolute paths (os.PathLike) or groups (starting with a colon).
	"""
	include = {*itertools.chain(map(resolve_group, include or ()))}
	include = {*itertools.chain.from_iterable(map(expand_path, include))}
	exclude = {*itertools.chain(map(resolve_group, exclude or ()))}
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


def save(name=None, include=None, exclude=None, follow_symlinks=False, destination=None):
	"""
	The name is not validated in this function.
	
	If ``name`` is unspecified, the current profile's name is used.
	``include`` and ``exclude`` must be given in the same format as to ``paths_to_save()``.
	"""
	info = profile_info(name, convert_values=False)
	if name is None:
		if info is None:
			raise RuntimeError('Attempted to save the current profile, but no profile is active.')
		else:
			name = info['name']
	profile_dir = (constants.PROFILE_HOME / name) if destination is None else destination
	profile_dir.mkdir(parents=True, exist_ok=True)
	for path in map(Path, paths_to_save(include, exclude)):
		if not path.exists():
			sys.stderr.write(f'Warning: the path {path} doesn\'t exist. Skipping\n')
		elif not path.is_relative_to(Path.home()):
			sys.stderr.write(f'Warning: the path {path} is not within the user\'s home directory. Skipping\n')
		else:
			copy_path(path, profile_dir / path.relative_to(Path.home()), follow_symlinks=follow_symlinks)
	# TODO: implement git repos in profiles
	new_info = {
		'name': name,
		'author': info['author'] if info else None,
		'description': info['description'] if info else None,
		'groups': info['groups'] if info else []
	}
	with open(profile_dir / constants.PROFILE_INFO_FILENAME, 'w') as f:
		f.write(json.dumps(new_info))  # Write only after JSON serialization is successful


def load(name, include=None, exclude=None, overwrite_unsaved_configuration=False) -> bool:
	"""
	The name is not validated in this function.
	True is returned if the user canceled the action.
	
	The KDE configuration will be overwritten if:
		* ``overwrite_unsaved_configuration`` is True
			OR all of the following is true:
		* A profile is active
		* The source profile's info JSON is valid
		* The user manually confirmed that they want to overwrite their configuration
	"""
	profile_root = constants.PROFILE_HOME / name
	if overwrite_unsaved_configuration is not True:  # Be really sure that overwriting is intentional
		# If the checks below fail, exit the function.
		try:
			current_info = profile_info()
			assert (profile_root / constants.PROFILE_INFO_FILENAME).is_file()
			if current_info is None:
				print('Warning: there is no active profile, and the current configuration is NOT SAVED.')
			elif current_info['name'] != name:
				print('Warning: you\'re loading a new profile. Konfsave cannot check if the currently active profile has been updated with current files.')
			else:
				print('Warning: you\'re overwriting the current profile with existing configuration. Konfsave cannot check if the saved files are up-to-date.')
			if input('Are you sure you want to overwrite the current system configuration? [y/N]: ').lower() != 'y':
				print('Loading aborted.')
				return True
		except Exception as e:
			sys.stderr.write('Refusing to overwrite unsaved configuration\n')
			raise
	constants.CURRENT_PROFILE_PATH.unlink(missing_ok=True)
	for path in map(lambda p: Path(p).relative_to(Path.home()), paths_to_save(include, exclude)):
		source = profile_root / path
		if source.exists():
			copy_path(source, Path.home() / path)
		else:
			sys.stderr.write(f'Warning: the file {source} doesn\'t exist. Skipping\n')
	shutil.copyfile(profile_root / constants.PROFILE_INFO_FILENAME, constants.CURRENT_PROFILE_PATH)


def change(results, profile=None):
	"""
	``results`` is a dictionary containing modified attributes and their values.
	Attributes that exist in the profile but are not present in ``results`` will be kept as is.
	
	If the name is changed, ``rename()`` will be called. Additionally, if ``profile`` is
	the same as the current profile, the current profile's attributes will be changed as well.
	"""
	current = current_profile()
	if profile is None:
		if current is None:
			raise RuntimeError('Attempted to change the current profile, but no profile is active.')
		profile = current
	new_info = profile_info(profile, convert_values=False).copy()
	new_info.update(results)
	if profile == current:
		# Also modify the profile info stored in the home directory
		with open(constants.CURRENT_PROFILE_PATH, 'w') as f:
			f.write(json.dumps(new_info))
	if 'name' in results:
		rename(profile, results['name'], change_info=False)  # Avoid writing to the file twice
	with open(constants.PROFILE_HOME / new_info['name'] / constants.PROFILE_INFO_FILENAME, 'w') as f:
		f.write(json.dumps(new_info))  # Write only after JSON serialization is successful
		
		
def rename(source, result, change_info=True):
	"""
	Rename a saved profile by changing its info and directory. Only the resulting name is validated.
	The current profile is not modified even if its name matches the source name.
	"""
	validate_profile_name(result)
	if (constants.PROFILE_HOME / result).exists():
		raise FileExistsError(f'A profile named "{result}" is already saved.')
	if not (constants.PROFILE_HOME / source).exists():
		raise RuntimeError(f'The profile "{source}" doesn\'t exist.')
	if change_info:
		info = profile_info(source)
		info.update({'name': result})
		with open(constants.PROFILE_HOME / source / constants.PROFILE_INFO_FILENAME, 'w') as f:
			f.write(json.dumps(new_info))  # Write only after JSON serialization is successful
	(constants.PROFILE_HOME / source).rename(constants.PROFILE_HOME / result)


def delete(profile, clear_active=True, confirm=True) -> bool:
	"""
	If ``clear_active`` is True and the deleted profile has the same name as the active profile,
	the active profile info will be deleted as well. Current configuration will be unaffected.
	
	True is returned if the user canceled the action.
	"""
	if not (constants.PROFILE_HOME / profile).exists():
		sys.stderr.write(f'The profile "{profile}" doesn\'t exist.\n')
		return True
	if confirm:
		print(f'Warning: you\'re about to delete the profile "{profile}".')
		if input('Are you sure you want to permanently delete it? [y/N]: ') != 'y':
			print('Deleting aborted.')
			return True
	if clear_active and profile == current_profile():
		constants.CURRENT_PROFILE_PATH.unlink(missing_ok=True)
	shutil.rmtree(constants.PROFILE_HOME / profile)


_profile_info_cache = {}

def profile_info(profile_name=None, convert_values=True, use_cache=True) -> Optional[dict]:
	"""
	If the profile name is invalid, this function will print a warning and continue normally.
	
	When no argument is supplied, this will read ``constants.CURRENT_PROFILE_PATH``.
	The return value is ``None`` if the JSON file is missing or malformed.
	"""
	if use_cache and profile_name in _profile_info_cache:
		return _profile_info_cache[profile_name]
	if profile_name and not validate_profile_name(profile_name, exit_if_invalid=False):
		sys.stderr.write(f'Warning: "f{profile_info}" is an invalid profile name\n')
	try:
		info = parse_profile_info(
			(constants.PROFILE_HOME / profile_name / constants.PROFILE_INFO_FILENAME) \
				if profile_name else constants.CURRENT_PROFILE_PATH, convert_values=convert_values
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
			sys.stderr.write(f'Warning: malformed profile info at {profile_info_file}\n{str(e)} \n')
		return None
	
