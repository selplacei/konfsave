import sys
import argparse
from pathlib import Path
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
s[ave] [profile]                   Save the current configuration.
                                   If there is an active profile and its name is different from what's given here, the new name will overwrite it.
    --destination <path>           Instead of saving to the default location, copy files to a path.
    --follow-symlinks              By default, symlinks are copied as symlinks.
                                   If this option is given, the contents of symlinked files are copied instead.
    --include <files ...>          In addition to files included by default, include these files.
    --exclude <files ...>          If any of the given files would be included otherwise, exclude them.
                                   File paths for --include and --exclude must be inside the home directoy,
                                   and may be specified as relative to the home directory or absolute.
                                   Each profile can also specify its own list of additional files to include or exclude.
                                   These lists can be changed with `set-include` or `set-exclude`, respectively.
                                   The --include and --exclude flags will override such lists wherever conflicts occur.
                                   `save` will never attempt to delete files from existing saved profiles.
load <profile>                     Load a saved profile.
    --overwrite                    By default, loading will fail if the current configuration isn\'t saved. This will override it.
    --no-restart                   Unless this flag is given, the Plasma shell will restart after new configuration is loaded.
    --include <files ...>          Same as in `save`.
    --exclude <files ...>          Same as in `save`.
r[ename] <profile> <result>        Rename a profile.
set-include [profile] <files ...>  Set a profile-specific list of additional files to include by default.
set-exclude [profile] <files ...>  Set a profile-specific list of files to exclude by default.

For `save`, `set-include`, and `set-exclude`, specifying the profile is optional only if a profile is currently active.
'''
def validate_profile_name(name, exit_if_invalid=True) -> bool:
	valid = name.isidentifier()
	if not valid:
		sys.stderr.write(f'The profile name "{name}" is invalid.\n')
		if exit_if_invalid:
			sys.exit(1)
	return valid


def parse_arguments(argv):
	# Actions need to parsed separately because each action has its own
	# argument format, so different ArgumentParser objects have to be used.
	if argv[0] == 'python':
		argv = argv[1:]
	action = argv[1] if len(argv) > 1 else 'help'
	try:
		next(v for k, v in {
            ('-h', '--help', 'help'): lambda *_: print(HELP_TEXT),
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
	parser.add_argument(
		'profile', nargs='?', metavar='profile_name',
		help='If provided, prints detailed information about the profile.'
	)
	args = parser.parse_args(argv)
	if profile := args.profile:
		validate_profile_name(profile)
		info = profiles.profile_info(profile)
		if info is None:
			print(f'The profile {profile} doesn\'t exist.')
		else:
			print(f'Name: {info["name"]}')
			print(f'Stored at: {config.KONFSAVE_PROFILE_HOME / profile}')
			if include := info['include']:
				print(f'Files to additionally include: \n  {_N_T.join(include)}')
			if exclude := info['exclude']:
				print(f'Files to exclude by default: \n  {_N_T.join(exclude)}')
	else:
		if current_profile := profiles.current_profile():
			print(f'Current profile: {current_profile}')
			print(f'Stored at: {config.KONFSAVE_PROFILE_HOME / current_profile}')
		else:
			print(f'No profile is currently active.')
		if saved_profiles := list(map(lambda q: q.name, filter(
			lambda p: (p / config.KONFSAVE_PROFILE_INFO_FILENAME).exists(),
			config.KONFSAVE_PROFILE_HOME.glob('*')
		))):
			print(f'Saved profiles:\n  {_N_T.join(saved_profiles)}')
		else:
			print('No profiles are saved.')
	
	
def action_list_files(argv):
	parser = argparse.ArgumentParser(
		prog='konfsave list', add_help=True,
		description='Print a list of files that would be saved by \'konfsave save\'.'
	)
	parser.add_argument(
		'profile', nargs='?', default=profiles.current_profile(), metavar='profile_name',
		help='If provided, lists files that would be saved to a specific profile (according to its configuration).'
	)
	args = parser.parse_args(argv)
	if args.profile:
		validate_profile_name(args.profile)
	try:
		print('\n'.join(sorted(map(str, profiles.paths_to_save(args.profile)), key=str.lower)))
	except ValueError as e:
		print(str(e))


def action_save(argv):
	parser = argparse.ArgumentParser(prog='konfsave save', add_help=True)
	parser.add_argument('--profile', metavar='NAME')
	parser.add_argument('--destination', metavar='DEST', type=Path)
	parser.add_argument('--follow-symlinks', action='store_true', dest='follow_symlinks')
	parser.add_argument('--include', action='extend', nargs='*', metavar='FILE', type=Path)
	parser.add_argument('--exclude', action='extend', nargs='*', metavar='FILE', type=Path)
	args = parser.parse_args(argv)
	
	
	
def action_load(argv):
	...
	
	
def action_rename(argv):
	...
	
	
def action_set_files(argv):
	...
