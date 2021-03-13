import json
from pathlib import Path

from konfsave import constants
from konfsave import profiles


def save(name=None, include=None, exclude=None, follow_symlinks=False, destination=None):
	"""
	The name is not validated in this function.
	
	If ``name`` is unspecified, the current profile's name is used.
	Otherwise, the current profile will be switched to the result.
	``include`` and ``exclude`` must be given in the same format as to ``paths_to_save()``.
	"""
	info = profiles.profile_info(name, convert_values=False)
	if name is None:
		if info is None:
			raise RuntimeError('Attempted to save the current profile, but no profile is active.')
		else:
			name = info['name']
	profile_dir = (constants.PROFILE_HOME / name) if destination is None else destination
	profile_dir.mkdir(parents=True, exist_ok=True)
	for path in map(Path, profiles.paths_to_save(include, exclude)):
		if not path.exists():
			profiles.logger.info(f'The path {path} doesn\'t exist. Skipping')
		elif not path.is_relative_to(Path.home()):
			profiles.logger.warning(f'The path {path} is not within the user\'s home directory. Skipping')
		else:
			profiles.copy_path(path, profile_dir / path.relative_to(Path.home()), follow_symlinks=follow_symlinks)
	new_info = {
		'name': name,
		'author': info['author'] if info else None,
		'description': info['description'] if info else None,
		'groups': info['groups'] if info else []
	}
	with open(profile_dir / constants.PROFILE_INFO_FILENAME, 'w') as f:
		f.write(json.dumps(new_info))  # Write only after JSON serialization is successful
	with open(constants.CURRENT_PROFILE_PATH, 'w') as f:
		f.write(json.dumps(new_info))  # Write only after JSON serialization is successful 
