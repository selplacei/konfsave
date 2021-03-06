import configparser
from pathlib import Path

import constants

# The values referred to as "group names" include the preceding colon.
definitions = {}  # Mapping of group names to what they contain, as specified in the config
metagroups = {}  # Same as ``definitions``, but only contains metagroups (including redefined groups)
paths = {}  # Mapping of group names to the paths they contain, with sub-groups recursively broken down
			# Paths are stored as Path objects, absolute, and resolved
defaults = {  # Mapping of keys to values stored in the [Defaults] section, converted to applicable types
	'default-groups': []
}
