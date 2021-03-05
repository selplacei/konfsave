import sys
import argparse
import subprocess
import zipfile
from pathlib import Path
from typing import List

from . import constants
from . import profiles
from . import archive

_N_T = '\n  '  # Backslashes are not allowed in f-string expressions, so use a variable
HELP_TEXT = '''Konfsave is a KDE config manager.

usage: konfsave <action> [args ...] [flags ...]

Actions:
help, --help, -h    print this message and exit
i, info, ls         get info about the current configuration, or a profile if specified
s, save             save the current configuration
l, load             load a saved profile
c, change           modify a profile's attributes
a, archive          export a profile as a ZIP file
u, unarchive        import an archived profile
list-files          list files that save would copy

To see detailed usage instructions, run `konfsave <action> --help`.
All flags starting with '--' can be abbreviated.
'''
def parse_arguments(argv):
	# Actions need to parsed separately because each action has its own
	# argument format, so different ArgumentParser objects have to be used.
	if argv[0] == 'python':
		argv = argv[1:]
	action = argv[1] if len(argv) > 1 else 'help'
	try:
		next(v for k, v in {
            ('-h', '--help', 'help'): lambda *_: print(HELP_TEXT),
			('i', 'info', 'ls'): action_info,
			('list-files',): action_list_files,
			('s', 'save'): action_save,
			('l', 'load'): action_load,
			('c', 'change'): action_change,
			('d', 'delete'): action_delete,
			('a', 'archive'): action_archive,
			('u', 'unarchive'): action_unarchive
		}.items() if action in k)(argv[2:])
	except StopIteration:
		sys.stderr.write(f'Unrecognized action: {action}\nTry \'konfsave help\' for more info.\n')
	except KeyboardInterrupt:
		sys.stderr.write('Action cancelled.')
	

def action_info(argv):
	parser = argparse.ArgumentParser(prog='konfsave info')
	parser.add_argument(
		'profile', nargs='?', metavar='profile_name',
		help='If provided, prints detailed information about the profile.'
	)
	args = parser.parse_args(argv)
	if profile := args.profile:
		profiles.validate_profile_name(profile)
		info = profiles.profile_info(profile)
		if info is None:
			print(f'The profile {profile} doesn\'t exist.')
		else:
			print(f'Name: {info["name"]}')
			print(f'Stored at: {constants.KONFSAVE_PROFILE_HOME / profile}')
			if include := info['include']:
				print(f'Files to additionally include: \n  {_N_T.join(map(str, include))}')
			if exclude := info['exclude']:
				print(f'Files to exclude by default: \n  {_N_T.join(map(str, exclude))}')
	else:
		if current_profile := profiles.current_profile():
			print(f'Current profile: {current_profile}')
			print(f'Stored at: {constants.KONFSAVE_PROFILE_HOME / current_profile}')
		else:
			print(f'No profile is currently active.')
		# Choose directories which are valid profile names and contain an info file;
		# then, convert paths to names, and sort the final list of profiles.
		if saved_profiles := sorted(list(filter(lambda n: profiles.validate_profile_name(n, False), map(lambda q: q.name, filter(
			lambda p: (p / constants.KONFSAVE_PROFILE_INFO_FILENAME).exists(),
			constants.KONFSAVE_PROFILE_HOME.glob('*')
		)))), key=str.lower):
			print(f'Saved profiles:\n  {_N_T.join(saved_profiles)}')
		else:
			print('No profiles are saved.')
	
	
def action_list_files(argv):
	parser = argparse.ArgumentParser(
		prog='konfsave list',
		description='Print a list of files that would be saved by \'konfsave save\'.'
	)
	parser.add_argument(
		'profile', nargs='?', default=profiles.current_profile(), metavar='profile_name',
		help='If provided, lists files that would be saved to a specific profile (according to its configuration).'
	)
	args = parser.parse_args(argv)
	if args.profile:
		profiles.validate_profile_name(args.profile)
	try:
		print('\n'.join(sorted(map(str, profiles.paths_to_save(args.profile)), key=str.lower)))
	except ValueError as e:
		print(str(e))


def action_save(argv):
	parser = argparse.ArgumentParser(
		prog='konfsave save',
		# The default usage string puts "[name]" at the end, for some reason.
		usage='konfsave save [-h] [name] [--destination DEST] [--follow-symlinks] [--include [FILE ...]] [--exclude [FILE ...]]'
	)
	parser.add_argument(
		'profile', metavar='name', nargs='?', default=profiles.current_profile(),
		help='Save as the specified profile instead of using the currently loaded name. This is required if no profile is active.'
	)
	parser.add_argument(
		'--destination', metavar='DEST', type=Path,
		help='Instead of saving to Konfsave\'s profile storage, save to a specified destination.'
	)
	parser.add_argument(
		'--follow-symlinks', '-s', action='store_true', dest='follow_symlinks',
		help='By default, symlinks are copied as symlinks. If this flag is used, the contents of symlinked files will be copied.'
	)
	parser.add_argument(
		'--include', action='extend', nargs='*', metavar='FILE', default=[],
		help='Files to add to the profile. Paths must be either absolute or relative to the home directory. '
		'In either case, the actual file must be inside of the home directory.\n'
		'Files specified here will be included even if the profile excludes them by default.'
	)
	parser.add_argument(
		'--exclude', action='extend', nargs='*', metavar='FILE', default=[],
		help='Files to exclude from the profile; that is, they will not be copied,\n'
		'but if they already exist in the profile, they will not be deleted. Path format is the same as for --include. '
		'Files specified here will be excluded even if the profile includes them by default.'
	)
	args = parser.parse_args(argv)
	if args.profile:
		profiles.validate_profile_name(args.profile)
	if args.profile \
		and (constants.KONFSAVE_PROFILE_HOME / args.profile).exists() \
		and (current := profiles.profile_info()) \
		and current['name'] != args.profile:
			if input(f'Warning: the profile "{args.profile}" already exists. Are you sure you want to overwrite it? [y/N]: ') != 'y':
				return
	include = set()
	exclude = set()
	for path in map(Path, args.exclude):
		if not path.is_absolute():
			path = Path.home() / path
		exclude.add(path)
	for path in map(Path, args.include):
		if not path.is_absolute():
			path = Path.home() / path
		include.add(path)
	profiles.save(
		name=args.profile,
		destination=args.destination,
		follow_symlinks=args.follow_symlinks,
		include=include,
		exclude=exclude
	)
	print('Success')
	
	
def action_load(argv):
	parser = argparse.ArgumentParser(prog='konfsave load')
	parser.add_argument(
		'profile',
		help='The name of the profile to load.'
	)
	parser.add_argument(
		'--overwrite',
		help='By default, loading will fail if no profile is active (i.e. the current configuration is not saved). '
		'Otherwise, the user will be asked for confirmation. Using --overwrite will bypass both of these checks.'
	)
	parser.add_argument(
		'--no-restart', action='store_false', dest='restart',
		help='After loading a profile, the Plasma shell is restarted, unless this flag was specified.'
	)
	parser.add_argument(
		'--include', action='extend', nargs='*', metavar='FILE', default=[],
		help='Files to load from the profile in addition to those loaded by default. '
		'Paths must point to their final destination and be either absolute or relative to the home directory. '
		'Files that are loaded by default can be checked using `konfsave list <profile>`.'
	)
	parser.add_argument(
		'--exclude', action='extend', nargs='*', metavar='FILE', default=[],
		help='Files to not load from the profile. This overrides values specified by the profile\'s configuration. '
		'Path format is the same as for --include.'
	)
	args = parser.parse_args(argv)
	profiles.validate_profile_name(args.profile)
	include = set()
	exclude = set()
	for path in map(Path, args.exclude):
		if not path.is_absolute():
			path = Path.home() / path
		exclude.add(path)
	for path in map(Path, args.include):
		if not path.is_absolute():
			path = Path.home() / path
		include.add(path)
	success = not profiles.load(
		args.profile,
		include,
		exclude,
		overwrite_unsaved_configuration=args.overwrite
	)
	if success:
		if args.restart:
			subprocess.run(['sh', '-c', 'plasmashell --replace & disown'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			print('Plasma shell restarted')
			try:
				# Check if Kwin is running
				subprocess.run(['ps', '-C', 'kwin_x11'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			except subprocess.CalledProcessError:
				print('No running instance of Kwin detected')
			else:
				# If so, restart Kwin
				subprocess.run(['sh', '-c', 'kwin_x11 --replace & disown'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				print('Kwin restarted')
			try:
				# Check if Latte Dock is running
				subprocess.run(['ps', '-C', 'latte-dock'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			except subprocess.CalledProcessError:
				print('No running instance of Latte detected')
			else:
				# If so, restart Latte Dock
				subprocess.run(['sh', '-c', 'latte-dock --replace & disown'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				print('Latte restarted')
		print('Success')
	
	
def action_change(argv):
	parser = argparse.ArgumentParser(
		prog='konfsave change',
		epilog='Paths must be specified relative to the home directory.'
	)
	parser.add_argument(
		'profile', nargs='?',
		help='Profile to change. If not specified, the current profile will be used. '
		'Note that this will change the profile\'s saved attributes as well; '
		'if you\'d like to store new attributes as a separate profile, save the configuration under a new name first.'
	)
	parser.add_argument(
		'--name', help='New name for the profile.'
	)
	parser.add_argument(
		'--include', action='extend', nargs='*', metavar='FILE', default=[],
		help='New set of files to save to this profile in addition to those saved by default.'
	)
	parser.add_argument(
		'--exclude', action='extend', nargs='*', metavar='FILE', default=[],
		help='New set of files to NOT save to this profile even if they\'re saved by default.'
	)
	args = parser.parse_args(argv)
	results = {k: v for k, v in vars(args).items() if k != 'profile' and v}
	if results:
		profiles.change(results, args.profile)
		print('Success')
	else:
		print('Nothing to change')


def action_delete(argv):
	parser = argparse.ArgumentParser(
		prog='konfsave delete',
		description='Delete a profile. Current system configuration will be unchanged; '
		'however, if the deleted profile is active, there will no longer be an active profile.'
	)
	parser.add_argument(
		'profile', help='The profile to delete.'
	)
	parser.add_argument('--noconfirm', action='store_false', dest='confirm')
	args = parser.parse_args(argv)
	success = not profiles.delete(args.profile, confirm=args.confirm)
	if success:
		print('Success')


def action_archive(argv):
	parser = argparse.ArgumentParser(
		prog='konfsave archive', description='Export/archive a profile to share or import later.',
		# The default usage puts "profile" at the end
		usage='konfsave archive [-h] [profile] [--destination PATH] [--overwrite] [--compresslevel LEVEL] [--compression {store,lzma,deflate,bzip2}]'
	)
	parser.add_argument(
		'profile', nargs='?', help='The profile to archive.', default=profiles.current_profile()
	)
	parser.add_argument(
		'--destination', metavar='PATH', type=Path,
		help='The full path (including the filename) of the resulting archive. '
		f'By default, archives are saved as "[profile name].konfsave.zip" under the home directory.'
	)
	parser.add_argument(
		'--overwrite', action='store_true',
		help='Unless this option is specified, if the resulting file already exists, archiving will fail.'
	)
	parser.add_argument(
		'--compresslevel', type=int, default='9', metavar='LEVEL',
		help='How much to compress the archive, from 1 to 9 (9 by default). This has no effect if --compression is "store" or "lzma".'
	)
	parser.add_argument(
		'--compression', choices=['store', 'lzma', 'deflate', 'bzip2'], default='bzip2',
		help='Compression method (bzip2 by default). "store" means no compression.'
	)
	args = parser.parse_args(argv)
	compression = {
		'store': zipfile.ZIP_STORED,
		'lzma': zipfile.ZIP_LZMA,
		'deflate': zipfile.ZIP_DEFLATED,
		'bzip2': zipfile.ZIP_BZIP2
	}[args.compression]
	try:
		archive.archive_profile(
			profile=args.profile,
			overwrite=args.overwrite,
			destination=args.destination,
			compresslevel=args.compresslevel,
			compression=compression
		)
	except FileExistsError as e:
		sys.stderr.write(f'The file {e.filename} already exists.\n')
	except RuntimeError as e:
		sys.stderr.write(f'Error: {str(e)}\n')
	else:
		return
	sys.stderr.write(f'Archiving "{args.profile}" failed.')


def action_unarchive(argv):
	parser = argparse.ArgumentParser(
		prog='konfsave unarchive',
		description='Unpack and save a profile that was previously archived.',
		# The default usage puts "file" at the end
		usage='konfsave unarchive [-h] file [--name NAME] [--overwrite]'
	)
	parser.add_argument(
		'file', type=Path,
		help='Path to the archive to extract from.'
	)
	parser.add_argument(
		'--name', help='Extract to a specified profile name (by default, it\'s the same as the archived profile).'
	)
	parser.add_argument(
		'--overwrite', action='store_true',
		help='By default, if the destination profile already exists, the user will be asked for confirmation.'
		'Using this option will silently overwrite such profiles instead.'
	)
	args = parser.parse_args(argv)
	if args.name:
		profiles.validate_profile_name(args.name)
	if not archive.unarchive_profile(
		source=args.file,
		new_name=args.name,
		overwrite=args.overwrite
	):
		print('Success')
