#!/usr/bin/env python
import sys

from . import constants
from . import actions


if __name__ == '__main__':
	actions.parse_arguments(sys.argv)
