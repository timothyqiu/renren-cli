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
            html_to_plain_text(s.content).strip()
        )
    ]

    if s.root:
        content.append(
            u'> {}: {}'.format(
                s.root['owner']['name'],
                html_to_plain_text(s.root['content']).strip()
            )
        )

    content.append(
        u'Comments:{}\t{}'.format(
            s.comment_count, pretty_date(s.time)
        )
    )
    return u'\n'.join(content)


def list_status(args):
    client = Client()
    sheet, desc = client.get_status(page=args.page, page_size=args.page_size)

    if not sheet:
        print desc
        return

    if not args.status:
        print u'\n\n'.join(format_status(s) for s in sheet.status)
        return

    if not args.status - 1 in range(0, len(sheet.status)):
        print 'Status not found.'
        return

    # For a specific status
    status = sheet.status[args.status - 1]

    if args.comment:
        res, desc = client.post_status_comment(
            status.owner['id'], status.id, args.comment
        )

    print format_status(status)

    comments, desc = client.retrieve_status_comments(
        status.id, status.owner['id']
    )
    if not comments:
        print desc
    else:
        print u'\n'.join(
            u'* {}: {}'.format(
                cmt['owner']['name'],
                html_to_plain_text(cmt['content'])
            )
            for cmt in comments
        )


def interactive_list_status(args):
    client = Client()
    page = args.page
    while True:
        sheet, desc = client.get_status(page=page, page_size=args.page_size)

        if not sheet:
            print desc
            break

        print u'\n\n'.join(format_status(s) for s in sheet.status)

        action = raw_input('& ')

        if action == 'q':
            break
        elif action == '':
            page = page + 1
        else:
            print 'q - quit'
            print 'n, enter - continue'


def make_subparser(subparsers):
    parser = subparsers.add_parser('status', help='View and post status')
    parser.set_defaults(func=list_status)

    parser.add_argument('status', nargs='?', type=int)

    parser.add_argument('-p', '--page', default=1, type=int)
    parser.add_argument('--page-size', default=5, type=int)

    parser.add_argument('-c', '--comment')

    # test
    parser.add_argument('-i', help='interactive mode', dest='func',
                        action='store_const', const=interactive_list_status)


if __name__ == '__main__':
    pass
