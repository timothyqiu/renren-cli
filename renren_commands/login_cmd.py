#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Command Implementation for `login`
"""

__all__ = ['make_subparser']


import argparse
import getpass
import json

from renren_client import Client
from renren_config import Config


def login(args):
    client = Client()
    config = Config()

    email = args.email or config['email'] or raw_input('Email: ')
    password = args.email or config['password'] or getpass.getpass()

    success, desc = client.login(email, password)

    if success:
        print 'Login success.'
        client.save_cookies()
        print 'Cookies saved.'
        config['email'] = email
        config['password'] = password
    else:
        print 'Login failed:', desc


def make_subparser(subparsers):
    parser = subparsers.add_parser('login')
    parser.set_defaults(func=login)

    parser.add_argument('email', nargs='?')
    parser.add_argument('password', nargs='?')


if __name__ == '__main__':
    pass
