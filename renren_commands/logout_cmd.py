#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Command Implementation for `logout`
"""

__all__ = ['make_subparser']


import argparse
import os
import sys

from renren_client import Client


def logout(args):
    root = os.path.abspath(os.path.dirname(sys.argv[0]))
    path = os.path.join(root, Client.DEFAULT_COOKIES_FILENAME)

    if os.path.exists(path):
        os.remove(path)
        print 'Logged out.'
    else:
        print 'Not logged in. Nothing to do.'


def make_subparser(subparsers):
    parser = subparsers.add_parser('logout', help='Logout')
    parser.set_defaults(func=logout)


if __name__ == '__main__':
    pass
