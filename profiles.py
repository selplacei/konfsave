import sys
import json
from pathlib import Path

import config


def save(name=None):
	...
	
	
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
