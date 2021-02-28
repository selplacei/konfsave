import argparse
from typing import List

HELP_TEXT = '''Konfsave is a KDE config manager.

usage: konfsave action [args ...] [flags ...]

Actions:
help, --help, -h                   Print this message.
info [profile]                     Get info about a profile if specified. Otherwise, show the active profile and list saved profiles.
list-files [profile]               List the files that `save` would copy given current circumstances.
save [profile]                     Save the current configuration to a profile.
    --destination <path>           Instead of saving to the default location, copy files to a path.
    --follow-symlinks              By default, symlinks are copied as symlinks.
								   If this option is given, the contents of symlinked files are copied instead.
    --include <files ...>          In addition to files included by default, include these files.
    --exclude <files ...>          If any of the given files would be included otherwise, exclude them.
                                   File paths for --include and --exclude must be relative to the home directory or absolute.
                                   Each profile can also specify its own list of additional files to include or exclude.
                                   These lists can be changed with `set-include` or `set-exclude`, respectively.
                                   The --include and --exclude flags will override such lists wherever conflicts occur.
                                   `save` will never delete files from existing saved profiles.
load <profile>                     Load a saved profile.
    --overwrite                    By default, loading will fail if the current configuration isn\'t saved. This will override it.
    --no-restart                   Unless this flag is given, the Plasma shell will restart after new configuration is loaded.
    --include <files ...>          Same as in `save`.
    --exclude <files ...>          Save as in `save`.
rename <profile> <result>          Rename a profile.
set-include [profile] <files ...>  Set a profile-specific list of additional files to include by default.
set-exclude [profile] <files ...>  Set a profile-specific list of files to exclude by default.

For `save`, `set-include`, and `set-exclude`, specifying the profile is optional only if a profile is currently active.
'''

profile: str = None			# Name of the profile to work with
include: List[str] = []		# save/load: custom include list; set-include: new include list
exclude: List[str] = []		# save/load: custom exclude list; set-exclude: new exclude list
overwrite: bool = False		# load: whether existing unsaved configuration should be overwritten
destination: str = None		# save: profile directory; rename: result
follow_symlinks = False		# save: False if symlinks should be kept as symlinks
git_remote: str = None		# upload/download/set-remote: the remote to work with


def parse_arguments(argv):
    ...    
