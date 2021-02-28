import argparse
from typing import Literal

action: typing.Literal[
	'help',			# Print information about the program
	'info',			# Get info about a profile
	'save',			# Save current configuration to a profile
	'load',			# Load configuration from a profile
	'rename',		# Rename a profile
	'set-remote',	# Set a profile's remote
	'upload',		# Upload a profile to a remote
	'download',		# Clone a profile from a remote
	] = 'help'


def parse_arguments():
	...
