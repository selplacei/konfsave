import shutil
import subprocess
import time
from pathlib import Path

from konfsave import constants
from konfsave import config
from konfsave import profiles


def load(name, include=None, exclude=None, overwrite_unsaved_configuration=False, restart=True) -> bool:
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
	profile_root = config.profile_home / name
	if overwrite_unsaved_configuration is not True:  # Be really sure that overwriting is intentional
		# If the checks below fail, exit the function.
		try:
			current_info = profiles.profile_info()
			assert (profile_root / config.profile_info_filename).is_file()
			if current_info is None:
				print(
					'Warning: there is no active profile, and the current configuration is NOT SAVED.'
				)
			elif current_info['name'] != name:
				print(
					'Warning: you\'re loading a new profile. Konfsave cannot check if the currently '
					'active profile has been updated with current files.'
				)
			else:
				print(
					'Warning: you\'re overwriting the current profile with existing configuration. '
					'Konfsave cannot check if the saved files are up-to-date.'
				)
			if input(
				'Are you sure you want to overwrite the current system configuration? [y/N]: '
			).lower() != 'y':
				print('Loading aborted.')
				return True
		except Exception as e:
			profiles.logger.error('Refusing to overwrite unsaved configuration due to an error')
			raise
	if restart:
		restart_list = []
		subprocess.run(
			['kquitapp5', 'plasmashell'],
			stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
		)
		try:
			# Check if Latte Dock is running
			subprocess.run(
				['ps', '-C', 'latte-dock'],
				check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
			)
		except subprocess.CalledProcessError:
			profiles.logger.info('No running instance of Latte detected')
		else:
			subprocess.run(['kquitapp5', 'lattedock'])
			restart_list.append('latte-dock')
	config.current_profile_path.unlink(missing_ok=True)
	for path in map(
		lambda p: Path(p).relative_to(Path.home()),
		profiles.paths_to_save(include, exclude)
	):
		source = profile_root / path
		if source.exists():
			profiles.copy_path(source, Path.home() / path)
		else:
			profiles.logger.info(f'The file {source} doesn\'t exist. Skipping\n')
	shutil.copyfile(profile_root / config.profile_info_filename, config.current_profile_path)
	if restart:
		subprocess.run(
			['kstart5', 'plasmashell'],
			stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
		)
		try:
			# Check if Kwin is running
			subprocess.run(
				['ps', '-C', 'kwin_x11'],
				check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
			)
		except subprocess.CalledProcessError:
			profiles.logger.info('No running instance of KWin detected')
		else:
			# If so, reload Kwin
			subprocess.run(
				['dbus-send', '--session', '--dest=org.kde.KWin', '/KWin', 'org.kde.KWin.reloadConfig'],
				stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
			)
		if 'latte-dock' in restart_list:
			time.sleep(3)  # Allow KWin to completely restart
			subprocess.run(
				['kstart5', 'latte-dock'],
				stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
			) 
