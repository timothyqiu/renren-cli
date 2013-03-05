#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Command Implementation for `config`
"""

__all__ = ['make_subparser']


import argparse

from renren_config import Config


def list_config(args):
    print unicode(Config())


def clear_config(args):
    Config().clear()


def make_subparser(subparsers):
    parser = subparsers.add_parser('config', help='Get and set config')
    parser.set_defaults(func=list_config)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--clear', dest='func', help='clear config',
                       action='store_const', const=clear_config)


if __name__ == '__main__':
    pass
