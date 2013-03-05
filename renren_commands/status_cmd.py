#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Command Implementation for `status`
"""

__all__ = ['make_subparser']


import argparse

from renren_client import Client


def list_status(args):
    client = Client()
    success, desc = client.get_status(page=args.page, page_size=args.page_size)
    print unicode(desc)


def make_subparser(subparsers):
    parser = subparsers.add_parser('status', help='View and post status')
    parser.set_defaults(func=list_status)

    parser.add_argument('-p', '--page', default=1, type=int)
    parser.add_argument('--page-size', default=5, type=int)


if __name__ == '__main__':
    pass
