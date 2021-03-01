import sys
import os
import shutil
import json
from pathlib import Path
from typing import Optional, Set

import config
# TODO: write proper docstrings so that this can be used as a library

def copy_path(source, destination, overwrite=True, follow_symlinks=False):
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
		with open(config.KONFSAVE_CURRENT_PROFILE_PATH, 'r') as f:
			return f.read().strip()
	except FileNotFoundError:
		return None


def paths_to_save(name=None, include=None, exclude=None, default_include=None, nonexisting_ok=False) -> Set[Path]:
	"""
	``include``, ``exclude``, and ``default_include`` must be given as absolute paths
	Paths are returned as absolute and resolved
	If ``name`` is not specified, the current profile will be used if one is active;
	otherwise, the default list from config.py is used
	"""
	default_include = set(map(lambda p: Path(p).resolve(), default_include or config.PATHS_TO_SAVE))
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
	If ``name`` is unspecified, the current configuration is saved.
	``include`` and ``exclude`` must be given in the same format as to ``paths_to_save()``.
	"""
	info = profile_info(name)
	if name is None:
		if info is None:
			raise RuntimeError('Attempted to save the current profile, but no profile is active.')
		else:
			name = info['name']
	profile_dir = (config.KONFSAVE_PROFILE_HOME / name) if destination is None else destination
	profile_dir.mkdir(parents=True, exist_ok=True)
	for path in map(Path, paths_to_save(name, include, exclude, nonexisting_ok=True)):
		print(f'Copying {path}')
		if not path.exists():
			sys.stderr.write(f'Warning: this path doesn\'t exist. Skipping\n')
		elif not path.is_relative_to(Path.home()):
			sys.stderr.write(f'Warning: this path is not within the user\'s home directory. Skipping\n')
		else:
			copy_path(path, profile_dir / path.relative_to(Path.home()), follow_symlinks=follow_symlinks)
	# TODO: implement git repos in profiles
	new_info = {
		'name': name,
		'include': info['include'] if info else [],
		'exclude': info['exclude'] if info else []
	}
	with open(profile_dir / config.KONFSAVE_PROFILE_INFO_FILENAME, 'w') as f:
		json.dump(new_info, f)


def load(name, include=None, exclude=None, overwrite_unsaved_configuration=False):
	"""
	The KDE configuration will be overwritten if:
		* ``overwrite_unsaved_configuration`` is True
			OR all of the following is true:
		* There is a ``current_profile`` file in ``{KONFSAVE_DATA_PATH}``
		* A profile with the same name is saved
		* The two profiles' latest Git commits have the same hash
	"""
	profile_root = config.KONFSAVE_PROFILE_HOME / name
	if overwrite_unsaved_configuration is not True:  # Be really sure that overwriting is intentional
		# If the checks below fail, exit the function.
		try:
			current_info = profile_info()
			assert current_info is not None
			source_info = profile_info(name)
			assert source_info is not None
			if current_info['name'] != source_info['name']:
				print('Warning: you\'re loading a new profile. Konfsave cannot check if every existing file has been saved.')
				if input('Are you sure you want to overwrite the current configuration? [y/N]: ').lower() != 'y':
					print('Loading aborted.')
					return
		except Exception as e:
			sys.stderr.write('Refusing to overwrite unsaved configuration\n')
			raise
	config.KONFSAVE_CURRENT_PROFILE_PATH.unlink(missing_ok=True)
	for path in map(lambda p: Path(p).relative_to(Path.home()), paths_to_save(name, include, exclude)):
		(f'Copying {path}')
		source = profile_root / path
		if source.exists():
			copy_path(source, Path.home() / path)
		else:
			sys.stderr.write(f'Warning: the file {source} doesn\'t exist. Skipping\n')
	shutil.copyfile(profile_root / config.KONFSAVE_PROFILE_INFO_FILENAME, config.KONFSAVE_CURRENT_PROFILE_PATH)


def profile_info(profile_name=None) -> Optional[dict]:
	"""
	When no argument is supplied, this will read ``config.KONFSAVE_CURRENT_PROFILE_PATH``.
	The return value is ``None`` if the JSON file is missing or malformed.
	"""
	try:
		return parse_profile_info(
			(config.KONFSAVE_PROFILE_HOME / profile_name / config.KONFSAVE_PROFILE_INFO_FILENAME) \
				if profile_name else config.KONFSAVE_CURRENT_PROFILE_PATH
		)
	except FileNotFoundError:
		return None


def parse_profile_info(profile_info_file_path) -> Optional[dict]:
	try:
		with open(profile_info_file_path) as f:
			info = json.load(f)
			assert info['name'].isidentifier()
			info['include'] = set(map(Path, info['include'] or ()))
			info['exclude'] = set(map(Path, info['exclude'] or ()))
			return info
	except (json.JSONDecodeError, KeyError, AssertionError) as e:
		sys.stderr.write(f'Warning: malformed profile info at {profile_info_file_path};\n{str(e)}\n')
		return None
	
