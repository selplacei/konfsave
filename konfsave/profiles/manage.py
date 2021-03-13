import json
import shutil
from pathlib import Path
from typing import Union, Iterable

from konfsave import config
from konfsave import profiles


def change(results, profile=None):
	"""
	``results`` is a dictionary containing modified attributes and their values.
	Attributes that exist in the profile but are not present in ``results`` will be kept as is.
	
	If the name is changed, ``rename()`` will be called. Additionally, if ``profile`` is
	the same as the current profile, the current profile's attributes will be changed as well.
	"""
	current = profiles.current_profile()
	if profile is None:
		if current is None:
			raise RuntimeError(
				'Attempted to change the current profile, but no profile is active. Try saving or '
				'loading something first, or specifying which saved profile you\'d like to change.'
			)
		profile = current
	new_info = profiles.profile_info(profile, convert_values=False).copy()
	new_info.update(results)
	if profile == current:
		# Also modify the profile info stored in the home directory
		with open(config.current_profile_path, 'w') as f:
			f.write(json.dumps(new_info))
	if 'name' in results:
		rename(profile, results['name'], change_info=False)  # Avoid writing to the file twice
	with open(config.profile_home / new_info['name'] / config.profile_info_filename, 'w') as f:
		f.write(json.dumps(new_info))  # Write only after JSON serialization is successful
		
		
def rename(source, result, change_info=True):
	"""
	Rename a saved profile by changing its info and directory. Only the resulting name is validated.
	The current profile is not modified even if its name matches the source name.
	"""
	profiles.validate_profile_name(result)
	if (config.profile_home / result).exists():
		raise FileExistsError(f'A profile named "{result}" is already saved.')
	if not (config.profile_home / source).exists():
		raise RuntimeError(f'The profile "{source}" doesn\'t exist.')
	if change_info:
		info = profiles.profile_info(source)
		info.update({'name': result})
		with open(config.profile_home / source / config.profile_info_filename, 'w') as f:
			f.write(json.dumps(new_info))  # Write only after JSON serialization is successful
	(config.profile_home / source).rename(config.profile_home / result)


def delete(profile: Union[str, Iterable[str]], clear_active=True, confirm=True) -> bool:
	"""
	``profile`` may be a string specifying a single profile to delete, or a list of profiles.
	
	If ``clear_active`` is True and the deleted profile has the same name as the active profile,
	the active profile info will be deleted as well. Current configuration will be unaffected.
	
	True is returned if the user canceled the action, or if it is otherwise unsuccessful.
	"""
	if not isinstance(profile, str):
		profile = list(profile)
		if len(profile) > 1:
			_profile_list = ', '.join(map(lambda n: f'"{n}"', profile))
			if confirm:
				print(f'Warning: you\'re about to delete the profiles {_profile_list}.')
				if input('Are you sure you want to permanently delete all of them? [y/N]: ') != 'y':
					print('Deleting aborted.')
					return True
			for prf in profile:
				delete(prf, clear_active=clear_active, confirm=False)
			return
		elif len(profile) == 1:
			profile = profile[0]
		else:
			profiles.logger.error('The list of profiles to delete is empty.')
			return True
	if not (config.profile_home / profile).exists():
		profiles.logger.error(f'The profile "{profile}" doesn\'t exist.')
		return True
	if confirm:
		print(f'Warning: you\'re about to delete the profile "{profile}".')
		if input('Are you sure you want to permanently delete it? [y/N]: ') != 'y':
			print('Deleting aborted.')
			return True
	if clear_active and profile == profiles.current_profile():
		config.current_profile_path.unlink(missing_ok=True)
	shutil.rmtree(config.profile_home / profile)
	print(f'Deleted profile "{profile}"')
