import sys
import shutil
import json
from pathlib import Path
from typing import Optional, Set

import config


def paths_to_save(name=None, include=None, exclude=None, default_include=None) -> Set[str]:
	default_include = default_include or config.PATHS_TO_SAVE
	include = set(include)
	exclude = set(exclude)
	if name is None:
		info = profile_info()
		if info is None:
			raise RuntimeError('Attempted to save the current profile, but no profile is active.')
		name = info['name']
	else:
		info = profile_info(config.KONFSAVE_DATA_PATH / name / 'info.json')
	exclude = (exclude | info['exclude']) - include
	include = include | info['include'] - exclude
	return (default_include | include) - exclude


def save(name=None, include=None, exclude=None, follow_symlinks=True):
	"""
	If ``name`` is unspecified, the current configuration is saved.
	If ``name`` is unspecified and any of the other arguments are not empty, they are combined
	with the data stored in the current profile, with priority given to the argument.
	"""
	profile_dir = config.KONFSAVE_DATA_PATH / name
	profile_dir.mkdir(parents=True)
	files_to_save = []
	for path in paths_to_save(name, include, exclude):
		files_to_save += Path(path).glob('**')
	for path in files_to_save:
		print(f'Copying {path}')
		if not path.exists():
			sys.stderr.write(f'Error: this path doesn\'t exist. Skipping')
		elif not path.is_relative_to(Path.home()):
			sys.stderr.write(f'Error: this path is not within the user\'s home directory. Skipping')
		else:
			shutil.copy(Path.home() / path, profile_dir / path, follow_symlinks=follow_symlinks)
	# TODO: implement git repos in profiles


def load(name, overwrite_unsaved_configuration=False):
	"""
	The KDE configuration stored in ``homedir`` will be overwritten if:
		* ``overwrite_unsaved_configuration`` is True
			OR all of the following is true:
		* There is a ``current_profile`` file in ``{KONFSAVE_DATA_PATH}``
		* A profile with the same name is saved
		* The two profiles' latest Git commits have the same hash
	"""
	...


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
			assert info['latest_commit_hash']			# Must not be empty
			assert isinstance(info['include'], list)	# May be an empty list
			assert isinstance(info['exclude'], list)	# May be an empty list
			return info
	except (json.JSONDecodeError, KeyError, AssertionError) as e:
		sys.stderr.write(f'Warning: malformed profile info at {path};\n{str(e)}')
		return None
	except FileNotFoundError:
		# The current configuration is not saved. Consider this normal behavior.
		return None
	
