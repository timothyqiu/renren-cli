#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Command Implementation for `status`
"""

__all__ = ['make_subparser']


import argparse
import getpass

from renren_client import Client


def list_status(args):
    client = Client()
    print client.get_status(page=args.page)


def make_subparser(subparsers):
    parser = subparsers.add_parser('status')
    parser.set_defaults(func=list_status)

    parser.add_argument('--page', default=0, type=int)


if __name__ == '__main__':
    pass
