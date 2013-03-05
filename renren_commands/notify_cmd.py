#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Command Implementation for `notify`
"""

__all__ = ['make_subparser']


import argparse

from renren_client import Client


def list_notifications(args):
    client = Client()
    success, ntfs = client.get_notifications(page=args.page)

    for ntf in ntfs:
        print unicode(ntf)


def make_subparser(subparsers):
    parser = subparsers.add_parser('notify', help='View notifications')
    parser.set_defaults(func=list_notifications)

    parser.add_argument('--page', default=1, type=int)


if __name__ == '__main__':
    pass
