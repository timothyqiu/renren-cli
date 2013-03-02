#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Reference: http://s.xnimg.cn/a52197/n/apps/login/login-v6.js

from datetime import datetime
import cookielib
import os
import re
import logging
import json
import urllib
import urllib2


class LoginEncryptor:

    URL_GET_ENCRYPT_KEY = 'http://login.renren.com/ajax/getEncryptKey'

    CACHE_FILENAME = '.renren.login.encryptor.cache'

    def __init__(self):
        if os.path.exists(self.CACHE_FILENAME):
            self.loadKeys()
        else:
            self.retrieveKeys()

    def saveKeys(self, keys):
        with open(self.CACHE_FILENAME, 'wb') as f:
            json.dump(keys, f)

    def loadKeys(self):
        if os.path.exists(self.CACHE_FILENAME):
            with open(self.CACHE_FILENAME, 'rb') as f:
                keys = json.load(f)
            self.update(keys)
        else:
            logging.warn('%s does not exist.' % self.CACHE_FILENAME)

    def retrieveKeys(self):
        response = urllib2.urlopen(self.URL_GET_ENCRYPT_KEY)
        res = json.loads(response.read())
        self.update(res)
        self.saveKeys(res)

    def update(self, res):
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
    URL_NOTIFICATION = \
        'http://notify.renren.com/rmessage/get?getbybigtype=1&bigtype=1&view=16'

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.encryptor = LoginEncryptor()

        self.cookiejar = cookielib.CookieJar()
        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cookiejar)
        )

    def post(self, url, data):
        body = urllib.urlencode(data)

        logging.info('POST %s' % url)

        request = urllib2.Request(url, body)
        response = self.opener.open(request)
        return response.read()

    def get(self, url, data={}):
        body = urllib.urlencode(data)
        if body:
            seperator = '&' if '?' in url else '?'
            url += seperator + body

        logging.info('GET %s' % url)

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

            # For ajax, it seems that we always need requestToken and _rtk,
            # which comes from the global XN.get_check and XN.get_check_x.
            # These values can be found in source code of each page (probably).
            html = self.get(res['homeUrl'])
            checkMatch = re.search(r'get_check:\'(.*?)\'', html)
            checkXMatch = re.search(r'get_check_x:\'(.*?)\'', html)
            if checkMatch and checkXMatch:
                self.get_check = checkMatch.group(1)
                self.get_check_x = checkXMatch.group(1)
            else:
                print 'Get token failed'
        else:
            print 'Login failed'
            print res['failDescription']

    def getCommentNotifications(self, start=0, limit=20):
        data = {
            'begin': start,
            'limit': limit,
        }
        res = json.loads(self.get(self.URL_NOTIFICATION, data))
        logging.info('Comment notification count: %d' % len(res))
        result = []
        for ntf in res:
            result.append(parseCommentNotification(ntf))
        return result


def parseCommentNotification(ntf):
    timestamp = float(ntf['time'])
    content = ntf['content']

    notification = {
        'id': ntf['nid'],
        'unread': int(ntf['unread']) > 0,
        'time': datetime.fromtimestamp(timestamp),
        'removeCallback': ntf['rmessagecallback'],
        'processCallback': ntf['processcallback'],
    }

    links = re.findall(r'<a.*?href="https?://(.*?)\..*?".*?>(.*?)</a>', content)

    notification['nickname'] = links[0][1]
    notification['type'] = links[1][0]
    notification['description'] = links[1][1]

    return notification


if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__) or '.')

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s')

    with open('config.json', 'rb') as f:
        config = json.load(f)

    email = config['email']
    password = config['password']

    client = RenrenClient(email, password)
    client.login()

    notifications = client.getCommentNotifications()
    for n in notifications:
        print '%s %s %s %-8s %s\t%s' % \
        (n['id'], n['time'], n['unread'], n['type'], n['nickname'], n['description'])
