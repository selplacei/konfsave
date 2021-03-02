import sys
import os
import shutil
import json
from pathlib import Path
from typing import Optional, Set

from . import constants
# TODO: write proper docstrings so that this can be used as a library

def validate_profile_name(name, exit_if_invalid=True) -> bool:
	valid = name.isidentifier()
	if (not valid) and exit_if_invalid:
		sys.stderr.write(f'The profile name "{name}" is invalid.\n')
		sys.exit(1)
	return valid


def copy_path(source, destination, overwrite=True, follow_symlinks=False):
	if constants.KONFSAVE_PRINT_COPYINGED_FILES:
		print(f'Copying {path}')
	destination.parent.mkdir(parents=True, exist_ok=True)
	if source.is_dir():
		shutil.copytree(
			src=source,
			dst=destination,
			symlinks=follow_symlinks,
			copy_function=shutil.copy,
			dirs_exist_ok=overwrite
		)
	else:
		if overwrite or not destination.exists():
			shutil.copy(source, destination, follow_symlinks=follow_symlinks)
			
			
def current_profile():
	try:
		return profile_info()['name']
	except TypeError:
		return None


def paths_to_save(name=None, include=None, exclude=None, default_include=None, nonexisting_ok=False) -> Set[Path]:
	"""
	The name is not validated in this function.
	
	``include``, ``exclude``, and ``default_include`` must be given as absolute paths
	Paths are returned as absolute and resolved
	If ``name`` is not specified, the current profile will be used if one is active;
	otherwise, the default list from config.ini is used
	"""
	default_include = set(map(lambda p: Path(p).resolve(), default_include or constants.PATHS_TO_SAVE))
	include = set(map(lambda p: Path(p).resolve(), include or ()))
	exclude = set(map(lambda p: Path(p).resolve(), exclude or ()))
	if not name:
		info = profile_info()
	else:
		info = profile_info(name)
		if info is None and not nonexisting_ok:
			raise ValueError(f'The profile "{name}" doesn\'t exist.')
	info = info or {'exclude': set(), 'include': set()}
	exclude = (exclude | set(map(lambda p: (Path.home() / p).resolve(), info['exclude']))) - include
	include = (include | set(map(lambda p: (Path.home() / p).resolve(), info['include']))) - exclude
	return (default_include | include) - exclude


def save(name=None, include=None, exclude=None, follow_symlinks=False, destination=None):
	"""
	The name is not validated in this function.
	
	If ``name`` is unspecified, the current profile's name is used.
	``include`` and ``exclude`` must be given in the same format as to ``paths_to_save()``.
	"""
	info = profile_info(name)
	if name is None:
		if info is None:
			raise RuntimeError('Attempted to save the current profile, but no profile is active.')
		else:
			name = info['name']
	profile_dir = (constants.KONFSAVE_PROFILE_HOME / name) if destination is None else destination
	profile_dir.mkdir(parents=True, exist_ok=True)
	for path in map(Path, paths_to_save(name, include, exclude, nonexisting_ok=True)):
		if not path.exists():
			sys.stderr.write(f'Warning: this path doesn\'t exist. Skipping\n')
		elif not path.is_relative_to(Path.home()):
			sys.stderr.write(f'Warning: this path is not within the user\'s home directory. Skipping\n')
		else:
			copy_path(path, profile_dir / path.relative_to(Path.home()), follow_symlinks=follow_symlinks)
	# TODO: implement git repos in profiles
	new_info = {
		'name': name,
		'include': list(info['include']) if info else [],
		'exclude': list(info['exclude']) if info else []
	}
	with open(profile_dir / constants.KONFSAVE_PROFILE_INFO_FILENAME, 'w') as f:
		json.dump(new_info, f)


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
	profile_root = constants.KONFSAVE_PROFILE_HOME / name
	if overwrite_unsaved_configuration is not True:  # Be really sure that overwriting is intentional
		# If the checks below fail, exit the function.
		try:
			current_info = profile_info()
			assert (profile_root / constants.KONFSAVE_PROFILE_INFO_FILENAME).is_file()
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
	constants.KONFSAVE_CURRENT_PROFILE_PATH.unlink(missing_ok=True)
	for path in map(lambda p: Path(p).relative_to(Path.home()), paths_to_save(name, include, exclude)):
		source = profile_root / path
		if source.exists():
			copy_path(source, Path.home() / path)
		else:
			sys.stderr.write(f'Warning: the file {source} doesn\'t exist. Skipping\n')
	shutil.copyfile(profile_root / constants.KONFSAVE_PROFILE_INFO_FILENAME, constants.KONFSAVE_CURRENT_PROFILE_PATH)


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
	new_info = profile_info(profile, convert_sets=False).copy()
	new_info.update(results)
	if profile == current:
		# Also modify the profile info stored in the home directory
		with open(constants.KONFSAVE_CURRENT_PROFILE_PATH, 'w') as f:
			f.write(json.dumps(new_info))
	if 'name' in results:
		rename(profile, results['name'], change_info=False)  # Avoid writing to the file twice
	with open(constants.KONFSAVE_PROFILE_HOME / new_info['name'] / constants.KONFSAVE_PROFILE_INFO_FILENAME, 'w') as f:
		f.write(json.dumps(new_info))  # Write only after JSON serialization is successful
		
		
def rename(source, result, change_info=True):
	"""
	Rename a saved profile by changing its info and directory. Only the resulting name is validated.
	The current profile is not modified even if its name matches the source name.
	"""
	validate_profile_name(result)
	if (constants.KONFSAVE_PROFILE_HOME / result).exists():
		raise FileExistsError(f'A profile named "{result}" is already saved.')
	if not (constants.KONFSAVE_PROFILE_HOME / source).exists():
		raise RuntimeError(f'The profile "{source}" doesn\'t exist.')
	if change_info:
		info = profile_info(source)
		info.update({'name': result})
		with open(constants.KONFSAVE_PROFILE_HOME / source / constants.KONFSAVE_PROFILE_INFO_FILENAME, 'w') as f:
			f.write(json.dumps(new_info))  # Write only after JSON serialization is successful
	(constants.KONFSAVE_PROFILE_HOME / source).rename(constants.KONFSAVE_PROFILE_HOME / result)


def delete(profile, clear_active=True, confirm=True) -> bool:
	"""
	If ``clear_active`` is True and the deleted profile has the same name as the active profile,
	the active profile info will be deleted as well. Current configuration will be unaffected.
	
	True is returned if the user canceled the action.
	"""
	if confirm:
		print(f'Warning: you\'re about to delete the profile "{profile}".')
		if input('Are you sure you want to permanently delete it? [y/N]: ') != 'y':
			print('Deleting aborted.')
			return True
	if clear_active and profile == current_profile():
		constants.KONFSAVE_CURRENT_PROFILE_PATH.unlink(missing_ok=True)
	shutil.rmtree(constants.KONFSAVE_PROFILE_HOME / profile)


def profile_info(profile_name=None, convert_sets=True) -> Optional[dict]:
	"""
	If the profile name is invalid, this function will print a warning and continue normally.
	
	When no argument is supplied, this will read ``constants.KONFSAVE_CURRENT_PROFILE_PATH``.
	The return value is ``None`` if the JSON file is missing or malformed.
	"""
	if profile_name and not validate_profile_name(profile_name, exit_if_invalid=False):
		sys.stderr.write(f'Warning: "f{profile_info}" is an invalid profile name\n')
	try:
		return parse_profile_info(
			(constants.KONFSAVE_PROFILE_HOME / profile_name / constants.KONFSAVE_PROFILE_INFO_FILENAME) \
				if profile_name else constants.KONFSAVE_CURRENT_PROFILE_PATH, convert_sets=convert_sets
		)
	except FileNotFoundError:
		return None


def parse_profile_info(profile_info_file_path, convert_sets=True) -> Optional[dict]:
	try:
		with open(profile_info_file_path) as f:
			info = json.load(f)
			assert info['name'].isidentifier()
			info['include'] = map(Path, info['include'] or ())
			info['exclude'] = map(Path, info['exclude'] or ())
			if convert_sets:
				info['include'] = set(info['include'])
				info['exclude'] = set(info['exclude'])
			else:
				info['include'] = list(info['include'])
				info['exclude'] = list(info['exclude'])
			return info
	except (json.JSONDecodeError, KeyError, AssertionError) as e:
		sys.stderr.write(f'Warning: malformed profile info at {profile_info_file_path}\n{str(e)}\n')
		return None
	
