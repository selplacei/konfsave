import sys
import os
import shutil
import json
from pathlib import Path
from typing import Optional, Set

import config


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


def paths_to_save(name, include=None, exclude=None, default_include=None) -> Set[str]:
	default_include = default_include or config.PATHS_TO_SAVE
	include = set(include or ())
	exclude = set(exclude or ())
	info = profile_info(config.KONFSAVE_PROFILE_HOME / name / 'info.json') or {'exclude': set(), 'include': set()}
	exclude = (exclude | info['exclude']) - include
	include = include | info['include'] - exclude
	return (default_include | include) - exclude


def save(name=None, include=None, exclude=None, follow_symlinks=False):
	"""
	If ``name`` is unspecified, the current configuration is saved.
	If ``name`` is unspecified and any of the other arguments are not empty, they are combined
	with the data stored in the current profile, with priority given to the argument.
	"""
	if name is None:
		info = profile_info()
		if info is None:
			raise RuntimeError('Attempted to save the current profile, but no profile is active.')
		name = info['name']
	profile_dir = config.KONFSAVE_PROFILE_HOME / name
	profile_dir.mkdir(parents=True, exist_ok=True)
	for path in map(Path, paths_to_save(name, include, exclude)):
		print(f'Copying {path}')
		if not path.exists():
			sys.stderr.write(f'Warning: this path doesn\'t exist. Skipping\n')
		elif not path.is_relative_to(Path.home()):
			sys.stderr.write(f'Warning: this path is not within the user\'s home directory. Skipping\n')
		else:
			destination = profile_dir / path.relative_to(Path.home())
			copy_path(path, destination, follow_symlinks=follow_symlinks)
	# TODO: implement git repos in profiles
	new_info = {
		'name': name,
		'hash': 'TODO',
		'include': include,
		'exclude': exclude
	}
	with open(profile_dir / 'info.json', 'w+') as f:
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
			source_info = profile_info(profile_root / 'info.json')
			assert current_info is not None
			assert source_info is not None
			assert current_info['name'] == source_info['name']
			assert current_info['hash'] == source_info['hash']
		except Exception as e:
			sys.stderr.write(f'Refusing to overwrite unsaved configuration')
			raise
	config.KONFSAVE_CURRENT_PROFILE_PATH.unlink(missing_ok=True)
	for path in map(lambda p: Path(p).relative_to(Path.home()), paths_to_save(name, include, exclude)):
		print(f'Copying {path}')
		source = profile_root / path
		if source.exists():
			copy_path(source, Path.home() / path)
		else:
			sys.stderr.write(f'Warning: this path doesn\'t exist. Skipping\n')
	shutil.copyfile(profile_root / 'info.json', config.KONFSAVE_CURRENT_PROFILE_PATH)


def profile_info(profile_info_file_path=None) -> Optional[dict]:
	"""
	When no argument is supplied, this will read ``config.KONFSAVE_CURRENT_PROFILE_PATH``.
	The return value is ``None`` if the JSON file is missing or malformed.
	"""
	path = profile_info_file_path or config.KONFSAVE_CURRENT_PROFILE_PATH
	try:
		with open(path) as f:
			info = json.load(f)
			assert info['name']							# Must not be empty
			assert info['hash']							# Must not be empty
			info['include'] = set(info['include'] or ())
			info['exclude'] = set(info['exclude'] or ())
			return info
	except (json.JSONDecodeError, KeyError, AssertionError) as e:
		sys.stderr.write(f'Warning: malformed profile info at {path};\n{str(e)}\n')
		return None
	except FileNotFoundError:
		# The current configuration is not saved. Consider this normal behavior.
		return None
	
