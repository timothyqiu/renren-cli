#!/usr/bin/env python2
# vim:fileencoding=utf-8

from datetime import datetime
import cookielib
import os
import re
import logging
import json
import urllib
import urllib2

from renren_encryptor import LoginEncryptor


class RenrenNotification:

    def __init__(self, data):
        self.parse_json(data)

    def parse_json(self, ntf):
        timestamp = float(ntf['time'])
        content = ntf['content']

        self.id = ntf['nid']
        self.unread = int(ntf['unread']) > 0
        self.time = datetime.fromtimestamp(timestamp)
        self.removeCallback = ntf['rmessagecallback']
        self.processCallback = ntf['processcallback']

        links = re.findall(r'<a.*?href="https?://(.*?)\..*?".*?>(.*?)</a>', content)

        self.nickname = links[0][1]
        self.type = links[1][0]
        self.description = links[1][1]


class RenrenClient:

    URL_CAPTCHA = \
        'http://icode.renren.com/getcode.do?t=web_login&rnd=Math.random()'
    URL_SHOW_CAPTCHA = 'http://www.renren.com/ajax/ShowCaptcha'
    URL_LOGIN = 'http://www.renren.com/ajaxLogin/login?1=1'
    URL_NOTIFICATION = \
        'http://notify.renren.com/rmessage/get?getbybigtype=1&bigtype=1&view=16'

    DEFAULT_COOKIES_FILENAME = '.renren.cookies'
    DEFAULT_TOKEN_URL = 'http://www.renren.com/siteinfo/about'

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.encryptor = LoginEncryptor()

        self.cookiejar = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cookiejar)
        )

        self.token = {}

        # automatic login
        if os.path.exists(self.DEFAULT_COOKIES_FILENAME):
            self.load_cookies()
            self.retrieve_token()
        else:
            if self.login():
                self.save_cookies();

    def save_cookies(self, filename=None):
        if not filename:
            filename = self.DEFAULT_COOKIES_FILENAME
        self.cookiejar.save(filename, ignore_discard=True)
        logging.info('Cookies saved to %s' % filename)

    def load_cookies(self, filename=None):
        if not filename:
            filename = self.DEFAULT_COOKIES_FILENAME
        self.cookiejar.revert(filename, ignore_discard=True)
        logging.info('Cookies loaded from %s' % filename)

    def retrieve_token(self, url=None):
        # For ajax, it seems that we always need requestToken and _rtk,
        # which comes from the global XN.get_check and XN.get_check_x.
        # These values can be found in source code of each page (probably).
        if not url:
            url = self.DEFAULT_TOKEN_URL
        html = self.get(url)
        checkMatch = re.search(r'get_check:\'(.*?)\'', html)
        checkXMatch = re.search(r'get_check_x:\'(.*?)\'', html)
        if checkMatch and checkXMatch:
            self.token['requestToken'] = checkMatch.group(1)
            self.token['_rtk'] = checkXMatch.group(1)
            logging.info('Token got from %s' % url)
        else:
            logging.warn('Token not found in %s' % url)

    def post(self, url, query={}):
        data = urllib.urlencode(query)

        logging.debug('POST %s' % url)

        request = urllib2.Request(url, data)
        response = self.opener.open(request)
        return response.read()

    def get(self, url, query={}):
        data = urllib.urlencode(query)
        if data:
            seperator = '&' if '?' in url else '?'
            url += seperator + data

        logging.debug('GET %s' % url)

        request = urllib2.Request(url)
        response = self.opener.open(request)
        return response.read()

    def get_icode(self):
        show = self.post(self.URL_SHOW_CAPTCHA, {'email': self.email})
        if show == '0':
            return ''
        return self.get_captcha()

    def get_captcha(self):
        captcha = self.get(self.URL_CAPTCHA)
        with open('captcha.jpg', 'wb') as image:
            image.write(captcha)
        return raw_input('Captcha: ')

    def login(self):
        data = {
            'email': self.email,
            'password': self.encryptor.encrypt(self.password),
            'rkey': self.encryptor.key['rkey'],
            'icode': self.get_icode(),
            'origURL': 'http://www.renren.com/home',
            'key_id': '1',
            'captcha_type': 'web_login',
            'domain': 'renren.com'
        }
        res = json.loads(self.post(self.URL_LOGIN, data))
        if res['code']:
            logging.info('Login success.')
            self.retrieve_token(res['homeUrl'])
            return True
        else:
            logging.error('Login failed: %s', res['failDescription'])
            return False

    def get_notifications(self, start=0, limit=20):
        data = {
            'begin': start,
            'limit': limit,
        }
        res = json.loads(self.get(self.URL_NOTIFICATION, data))
        ntfs = []
        for ntf in res:
            ntfs.append(RenrenNotification(ntf))
        return ntfs

    def remove_notification(self, nid):
        self.post('http://notify.renren.com/rmessage/remove?nl=' + nid,
                  self.token)

    def process_notification(self, nid):
        self.post('http://notify.renren.com/rmessage/process?nl=' + nid,
                  self.token)

    def retrieve_status_comments(self, status, me):
        data = {
            'owner': me,        # current account id
            'source': status,   # comment id
            't': 3,             # type: status
        }
        data = dict(data.items() + self.token.items())
        res = self.post('http://status.renren.com/feedcommentretrieve.do',
                        data)
        print json.loads(res)


def format_notification(ntf):
    unread = '*' if n.unread else ' '
    desc = n.description if n.type == 'status' else ' '
    return u'{:11} {:1} {:6} {:10} {}'.format(
        n.id, unread, n.type, n.nickname, desc
    )


if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__) or '.')

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s')

    with open('config.json', 'rb') as f:
        config = json.load(f)

    email = config['email']
    password = config['password']

    client = RenrenClient(email, password)

    ntfs = client.get_notifications()
    for n in ntfs:
        print format_notification(n)

    nid = raw_input('Remove which: ')
    if nid:
        client.remove_notification(nid)

    nid = raw_input('Process which: ')
    if nid:
        client.process_notification(nid)
