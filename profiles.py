import sys
import json
from pathlib import Path
from typing import Optional

import config


def save(name=None):
	if name is None:
	
	
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
			assert isinstance(info['include'], list)	# May be an empty list
			return info
	except (json.JSONDecodeError, KeyError, AssertionError) as e:
		sys.stderr.write(f'Warning: malformed profile info at {path};\n{str(e)}')
		return None
	except FileNotFoundError:
		# The current configuration is not saved. Consider this normal behavior.
		return None
	
