import sys
import argparse
from typing import List

import config
import profiles

_N_T = '\n  '  # Backslashes are not allowed in f-string expressions, so use a variable
HELP_TEXT = '''Konfsave is a KDE config manager.

usage: konfsave <action> [args ...] [flags ...]

Actions:
help, --help, -h                   Print this message.
i[nfo] [profile]                   Get info about a profile if specified. Otherwise, show the active profile and list saved profiles.
list[-files] [profile]             List the files that `save` would copy given current circumstances.
s[ave] [profile]                   Save the current configuration to a profile.
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
r[ename] <profile> <result>        Rename a profile.
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
	# Actions need to parsed separately because each action has its own
	# argument format, so different ArgumentParser objects have to be used.
	if argv[0] == 'python':
		argv = argv[1:]
	action = argv[1] if len(argv) > 1 else 'help'
	if action in ('help', '--help', '-h'):
		print(HELP_TEXT)
		return
	try:
		next(v for k, v in {
			('i', 'info'): action_info,
			('list', 'list-files'): action_list_files,
			('s', 'save'): action_save,
			('load'): action_load,
			('r', 'rename'): action_rename,
			('set-include', 'set-exclude'): action_set_files
		}.items() if action in k)(argv[2:])
	except StopIteration:
		sys.stderr.write(f'Unrecognized action: {action}\nTry \'konfsave help\' for more info.\n')
	

def action_info(argv):
	parser = argparse.ArgumentParser(prog='konfsave info', add_help=False)
	parser.add_argument('profile', nargs='?')
	args = parser.parse_args(argv)
	if profile := args.profile:
		info = profiles.profile_info(profile)
		if info is None:
			print(f'The profile {profile} doesn\'t exist.')
		else:
			print(f'Name: {info["name"]}')
			print(f'Stored at: {config.KONFSAVE_PROFILE_HOME / profile}')
			print(f'Files to include: \n  {_N_T.join(profiles.paths_to_save(profile))}')
			if include := info['include']:
				print(f'Of those, the following files are specific to this profile:')
				print(f'  {_N_T.join(include)}')
			if exclude := info['exclude']:
				print(f'Files to exclude: \n  {_N_T.join(exclude)}')
	else:
		if current_profile := profiles.current_profile():
			print(f'Current profile: {current_profile}')
		else:
			print(f'No profile is currently active.')
		if saved_profiles := list(map(lambda q: q.name, filter(
			lambda p: (p / '.konfsave_profile').exists(),
			config.KONFSAVE_PROFILE_HOME.glob('*')
		))):
			print(f'Saved profiles:\n  {_N_T.join(saved_profiles)}')
		else:
			print('No profiles are saved.')
	
	
def action_list_files(argv):
	...
	
	
def action_save(argv):
	...
	
	
def action_load(argv):
	...
	
	
def action_rename(argv):
	...
	
	
def action_set_files(argv):
	...
