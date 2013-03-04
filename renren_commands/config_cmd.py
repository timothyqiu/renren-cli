#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Command Implementation for `config`
"""

__all__ = ['make_subparser']


import argparse

from renren_config import Config


def config_list(args):
    print Config()


def make_subparser(subparsers):
    parser = subparsers.add_parser('config', help='Get and set config')
    parser.set_defaults(func=config_list)


if __name__ == '__main__':
    pass
