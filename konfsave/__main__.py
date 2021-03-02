#!/usr/bin/env python
import sys

from konfsave import constants
from konfsave import actions


def main():
	actions.parse_arguments(sys.argv)
	

if __name__ == '__main__':
	main()
