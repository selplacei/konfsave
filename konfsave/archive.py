import zipfile
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
