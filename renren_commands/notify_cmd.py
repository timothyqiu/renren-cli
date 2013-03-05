#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Command Implementation for `notify`
"""

__all__ = ['make_subparser']


import argparse

from renren_client import Client
from renren_utility import pretty_date, pad_str


def format_notification(n):
    marker = 'U' if n.unread else ' '
    return u'{} {} {:8} {:>15} {}'.format(
        marker, pad_str(n.nickname, 12), n.type,
        pretty_date(n.time), n.description
    )


def list_notifications(args):
    client = Client()
    ntfs, desc = client.get_notifications(
        page=args.page, page_size=args.page_size
    )

    if ntfs:
        print u'\n'.join(format_notification(n) for n in ntfs)
    else:
        print desc


def make_subparser(subparsers):
    parser = subparsers.add_parser('notify', help='View notifications')
    parser.set_defaults(func=list_notifications)

    parser.add_argument('-p', '--page', default=1, type=int)
    parser.add_argument('--page-size', default=15, type=int)


if __name__ == '__main__':
    pass
