#!/usr/bin/env python
import sys
import logging

from konfsave import constants
from konfsave import config
from konfsave import actions


def main():
	logging.basicConfig(format='[%(levelname)s] %(message)s')
	config.load_config()
	_constants = {k: str(v) for k, v in constants.__dict__.items() if k.isupper()}
	logging.getLogger('konfsave').debug(f'Constants: {_constants}')
	actions.parse_arguments(sys.argv)
	

if __name__ == '__main__':
	main()
