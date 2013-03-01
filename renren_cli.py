#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Reference: http://s.xnimg.cn/a52197/n/apps/login/login-v6.js

import cookielib
import os
import json
import urllib
import urllib2


class LoginEncryptor:

    URL_GET_ENCRYPT_KEY = 'http://login.renren.com/ajax/getEncryptKey'

    def getKeys(self):
        response = urllib2.urlopen(self.URL_GET_ENCRYPT_KEY)
        res = json.loads(response.read())
        self.rkey = res['rkey']
        self.e = int(res['e'], 16)
        self.n = int(res['n'], 16)
        self.chunkSize = self.getChunkSize(res['n'])

    def getChunkSize(self, n):
        for s in range(len(n) - 4, 0, -4):
            if int(n[s:s+4], 16) != 0:
                return s / 2
        return 0

    def encryptedString(self, value):
        # value to binary array and pad zero according to chunk size
        a = map(ord, value)
        a.extend([0] * (self.chunkSize - (len(a) % self.chunkSize)))

        # divide to fixed size chunks
        chunks = zip(* [iter(a)] * self.chunkSize)

        # hash chunks
        h = []
        for chunk in chunks:
            # make c integer form of a
            c = sum(chunk[i] << (i*8) for i in range(self.chunkSize))

            h.append('%x' % pow(c, self.e, self.n))
        return ' '.join(h)


class RenrenClient:

    URL_CAPTCHA = \
        'http://icode.renren.com/getcode.do?t=web_login&rnd=Math.random()'
    URL_SHOW_CAPTCHA = 'http://www.renren.com/ajax/ShowCaptcha'
    URL_LOGIN = 'http://www.renren.com/ajaxLogin/login?1=1'

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.encryptor = LoginEncryptor()
        self.encryptor.getKeys()

        self.cookiejar = cookielib.CookieJar()
        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cookiejar)
        )

    def post(self, url, data):
        body = '&'.join([
            urllib.quote(key) + '=' + urllib.quote(data[key])
            for key in data
        ])

        request = urllib2.Request(url, body)
        response = self.opener.open(request)
        return response.read()

    def get(self, url):
        request = urllib2.Request(url)
        response = self.opener.open(request)
        return response.read()

    def getICode(self):
        show = self.post(self.URL_SHOW_CAPTCHA, {'email': self.email})
        if show == '0':
            return ''
        return getCaptcha()

    def getCaptcha(self):
        captcha = self.get(self.URL_CAPTCHA)
        with open('captcha.jpg', 'wb') as image:
            image.write(captcha)
        return raw_input('Captcha: ')

    def login(self):
        data = {
            'email': self.email,
            'password': self.encryptor.encryptedString(self.password),
            'rkey': self.encryptor.rkey,
            'icode': self.getICode(),
            'origURL': 'http://www.renren.com/home',
            'key_id': '1',
            'captcha_type': 'web_login',
            'domain': 'renren.com'
        }
        res = json.loads(self.post(self.URL_LOGIN, data))
        if res['code']:
            print 'Login success'
            print 'Redirect to ' + res['homeUrl']
            self.get(res['homeUrl'])
        else:
            print res['failDescription']


if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__) or '.')

    with open('config.json', 'rb') as f:
        config = json.load(f)

    email = config['email']
    password = config['password']

    client = RenrenClient(email, password)
    client.login()
