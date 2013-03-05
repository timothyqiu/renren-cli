#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Command Implementation for `status`
"""

__all__ = ['make_subparser']


import argparse

from renren_client import Client
from renren_utility import pretty_date, html_to_plain_text


def format_status(s):
    content = [
        u'{}: {}'.format(
            s.owner['name'],
            html_to_plain_text(s.content)
        )
    ]

    if s.root:
        content.append(
            u'> {}'.format(html_to_plain_text(s.root['content']))
        )

    content.append(
        u'{}\tComments:{}'.format(
            pretty_date(s.time), s.comment_count
        )
    )
    return u'\n'.join(content)


def list_status(args):
    client = Client()
    sheet, desc = client.get_status(page=args.page, page_size=args.page_size)

    if sheet:
        print u'\n\n'.join(format_status(s) for s in sheet.status)
    else:
        print desc


def make_subparser(subparsers):
    parser = subparsers.add_parser('status', help='View and post status')
    parser.set_defaults(func=list_status)

    parser.add_argument('-p', '--page', default=1, type=int)
    parser.add_argument('--page-size', default=5, type=int)


if __name__ == '__main__':
    pass
