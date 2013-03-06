#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Command Implementation for `notify`
"""

__all__ = ['make_subparser']


import argparse

from renren_client import Client
from renren_utility import pretty_date, pad_str, get_display_len


def format_notifications(ntfs):
    namecols = max(get_display_len(n.nickname) for n in ntfs)

    text = []
    for n in ntfs:
        marker = 'U' if n.unread else ' '
        text.append(
            u'{} {} {:8} {:>15} {}'.format(
                marker, pad_str(n.nickname, namecols), n.type,
                pretty_date(n.time), n.description
            )
        )
    return u'\n'.join(text)


def list_notifications(args):
    client = Client()
    ntfs, desc = client.get_notifications(
        page=args.page, page_size=args.page_size
    )

    if ntfs:
        print format_notifications(ntfs)
    else:
        print desc


def make_subparser(subparsers):
    parser = subparsers.add_parser('notify', help='View notifications')
    parser.set_defaults(func=list_notifications)

    parser.add_argument('-p', '--page', default=1, type=int)
    parser.add_argument('--page-size', default=15, type=int)


if __name__ == '__main__':
    pass
