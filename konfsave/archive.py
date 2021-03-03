import sys
import zipfile
import shutil
import json
from pathlib import Path

from . import constants
from . import profiles


def archive_profile(profile, destination: Path = None, overwrite=False, compression=zipfile.ZIP_BZIP2, compresslevel=9):
	"""
	Archive a profile.
	
	If ``profile_dir`` isn't a valid profile, RuntimeError is raised.
	``destination`` should be a path pointing to the resulting .konfsave.zip file.
	If ``overwrite`` is False and the destination exists, ``FileExistsError`` will be raised.
	``compression`` and ``compresslevel`` are the same as in ``zipfile.ZipFile`` -
	see https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile for available values.
	"""
	open_mode = 'w' if overwrite else 'x'
	info = profiles.profile_info(profile)
	if info is None:
		raise RuntimeError(f'The directory {profile_dir} is not a valid Konfsave profile.')
	profile_dir = constants.KONFSAVE_PROFILE_HOME / profile
	destination = destination or (constants.KONFSAVE_ARCHIVE_DIRECTORY / (info['name'] + '.konfsave.zip'))
	with zipfile.ZipFile(destination, mode=open_mode, compression=compression, compresslevel=compresslevel) as zipf:
		print(f'Archiving "{profile}" into {destination}...')
		for source in profile_dir.glob('**/*'):
			zipf.write(source, arcname=source.relative_to(profile_dir))
	print('Archiving finished')


def unarchive_profile(source: Path, new_name=None, overwrite=False, confirm=True) -> bool:
	"""
	Extract and import an archived profile without loading it.
	Returns True if unarchiving wasn't successful.
	If ``new_name`` is unspecified, the original archive's profile name is validated.
	``new_name`` is not validated in this function.
	
	If ``confirm`` is True, the user will be warned about the safety implications of unarchiving,
	and the function will exit if they cancel. Additionally, if ``confirm`` is True,
	``overwrite`` is False, and the destination exists, the user will be asked whether they want
	to overwrite the existing profile; if yes, the profile will be overwritten.
	If ``confirm`` and ``overwrite`` are False and the destination exists, FileExistsError will be raised.
	If ``new_name`` is specified, the profile will be loaded into the matching directory and
	its info will be updated.
	If the original archive has no information file and ``new_name`` is unspecified, ValueError will be raised.
	"""
	with zipfile.ZipFile(source) as zipf:
		with zipf.open(constants.KONFSAVE_PROFILE_INFO_FILENAME) as infof:
			info = profiles.parse_profile_info(infof, convert_values=False)
			if info is None:
				sys.stderr.write(f'Warning: the archive {source} has a malformed {constants.KONFSAVE_PROFILE_INFO_FILENAME}.\n')
				if new_name is None:
					raise ValueError(f'Could not infer the destination profile name for archive {source}.')
			if new_name:
				info['name'] = new_name
			else:
				profiles.validate_profile_name(info['name'])
		if confirm and input(
			'Warning: you\'re about to extract a profile that may have been created by someone else.\n'
			'Konfsave profiles can contain any file within the home directory, not just KDE configurations.\n'
			'Unarchiving a profile will not load it; however, loading profiles from untrusted sources\n'
			'may have destructive consequences, including unintentionally overwriting personal data.\n'
			'Keep in mind that individual profiles can have their own list of files to include, '
			'and those are loaded even if they\'re not included in your config.ini.\n'
			'Have you manually gone through the archive and made sure that every file is expected? [y/N]: '
		) != 'y':
			print('Unarchiving aborted.')
			return True
		destination = constants.KONFSAVE_PROFILE_HOME / info['name']
		backup = None
		if destination.exists() and not overwrite:
			if confirm:
				if input(
					f'Warning: the profile "{info["name"]}" is already saved.\nAre you sure you want to overwrite it? [y/N]: '
				) != 'y':
					print('Unarchiving aborted.')
					return True
				else:
					# Create a backup, which will be deleted if all of the next steps are successful.
					backup = Path(str(destination) + '.bkp')
					if backup.exists():
						sys.stderr.write(f'Warning: the backup {backup} already exists. It will be overwritten.\n')
						shutil.rmtree(backup)  # Path.rename() fails if the directory is not empty
					destination.rename(str(destination) + '.bkp')
			else:
				raise FileExistsError(filename=str(destination))
		try:
			zipf.extractall(destination, members=(p for p in zipf.namelist() if p != constants.KONFSAVE_PROFILE_INFO_FILENAME))
			with open(destination / constants.KONFSAVE_PROFILE_INFO_FILENAME, 'w') as f:
				f.write(json.dumps(info))  # Write only after JSON serialization is successful
		except Exception as e:
			sys.stderr.write(f'Error: unarchiving failed.\n')
			if backup:
				sys.stderr.write(f'The previous version of "{info["name"]}" was backed up to {destination}\n')
			raise
		else:
			if backup:
				shutil.rmtree(backup)
