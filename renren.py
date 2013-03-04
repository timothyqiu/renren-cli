#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Renren Command-line Interface
"""

import argparse
import importlib
import logging
import re
import os
import sys


COMMAND_DIRECTORY = 'renren_commands'


def get_command_modules():
    """Get available command modules from COMMAND_DIRECTORY"""

    # find command files in sub directory
    path = os.path.join(os.path.dirname(sys.argv[0]), COMMAND_DIRECTORY)
    files = os.listdir(os.path.abspath(path))
    files = filter(lambda f: f.endswith('_cmd.py'), files)

    # import corresponding modules
    module_names = map(
        lambda f: '%s.%s' % (COMMAND_DIRECTORY, os.path.splitext(f)[0]),
        files
    )
    modules = map(importlib.import_module, module_names)

    # command modules should have a `make_subparser` function
    modules = filter(lambda m: getattr(m, 'make_subparser', None), modules)

    return modules


def parse_arguments():
    # fill in commands
    modules = get_command_modules()
    assert modules

    # build parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    for module in modules:
        module.make_subparser(subparsers)

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    args.func(args)
