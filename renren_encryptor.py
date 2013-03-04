#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Encryption Module for RenrenCLI
"""

__all__ = ['LoginEncryptor']


import json
import logging
import os
import urllib2


class LoginEncryptor:
    """This is an encryptor which is used to encrypt password when login. It
    seems to be an RSA Algorithm.

    Reference: http://s.xnimg.cn/a52197/n/apps/login/login-v6.js
    """

    DEFAULT_KEY_URL = 'http://login.renren.com/ajax/getEncryptKey'
    DEFAULT_KEY_FILENAME = '.renren.encryptor.login.key'

    def __init__(self):
        """Initialize the encryptor by trying to get key by the following
        order:

        1. Local file.
        2. Retrieve the key from web.

        If got from web, the key will be automatic saved."""
        if os.path.exists(self.DEFAULT_KEY_FILENAME):
            self.load_key()
        else:
            self.retrieve_key()
            self.save_key()

    def save_key(self, filename=None):
        if not filename:
            filename = self.DEFAULT_KEY_FILENAME
        with open(filename, 'wb') as f:
            json.dump(self.key, f)
        logging.info('Encrypt key saved to %s' % filename)

    def load_key(self, filename=None):
        if not filename:
            filename = self.DEFAULT_KEY_FILENAME
        with open(filename, 'rb') as f:
            self.key = json.load(f)
        logging.info('Encrypt key loaded from %s' % filename)

    def retrieve_key(self, url=None):
        if not url:
            url = self.DEFAULT_KEY_URL
        response = urllib2.urlopen(url)
        self.key = json.loads(response.read())
        logging.info('Encrypt key retrieved from %s' % url)

    def get_chunk_size(self):
        n = self.key['n']
        for s in range(len(n) - 4, 0, -4):
            if int(n[s:s+4], 16) != 0:
                return s / 2
        logging.error('Encryptor chunk size == 0')

    def encrypt(self, text):
        n = int(self.key['n'], 16)
        e = int(self.key['e'], 16)
        rkey = self.key['rkey']
        chunk_size = self.get_chunk_size()

        # value to binary array and pad zero according to chunk size
        a = map(ord, text)
        a.extend([0] * (chunk_size - (len(a) % chunk_size)))

        # divide to fixed size chunks
        chunks = zip(* [iter(a)] * chunk_size)

        # hash chunks
        cipher = []
        for chunk in chunks:
            # make c integer form of a
            msg = sum(chunk[i] << (i*8) for i in range(chunk_size))
            cipher.append('%x' % pow(msg, e, n))

        return ' '.join(cipher)


def test():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')

    pair = (
        'example.string',
        '2db4efad86a2db989c8b41adef828afb107e4e9866f23d461d1970e08269c669'
    )
    encryptor = LoginEncryptor()
    assert encryptor.encrypt(pair[0]) == pair[1], 'Wrong algorithm'

    print "Don't panic! Everything is fine."


if __name__ == '__main__':
    test()
