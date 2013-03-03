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

    FILENAME_COOKIES = '.renren.cookies'

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
        if os.path.exists(self.FILENAME_COOKIES):
            self.loadCookies()
            self.getToken()
        else:
            self.login()

    def saveCookies(self, filename=None):
        if not filename:
            filename = self.FILENAME_COOKIES
        self.cookiejar.save(filename, ignore_discard=True)

    def loadCookies(self, filename=None):
        if not filename:
            filename = self.FILENAME_COOKIES
        self.cookiejar.revert(filename, ignore_discard=True)

    def getToken(self, html=None):
        # For ajax, it seems that we always need requestToken and _rtk,
        # which comes from the global XN.get_check and XN.get_check_x.
        # These values can be found in source code of each page (probably).
        if not html:
            html = self.get('http://www.renren.com/siteinfo/about')
        checkMatch = re.search(r'get_check:\'(.*?)\'', html)
        checkXMatch = re.search(r'get_check_x:\'(.*?)\'', html)
        if checkMatch and checkXMatch:
            self.token['requestToken'] = checkMatch.group(1)
            self.token['_rtk'] = checkXMatch.group(1)
            logging.info('Got token')
        else:
            logging.warn('Get token failed')

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
            'password': self.encryptor.encrypt(self.password),
            'rkey': self.encryptor.key['rkey'],
            'icode': self.getICode(),
            'origURL': 'http://www.renren.com/home',
            'key_id': '1',
            'captcha_type': 'web_login',
            'domain': 'renren.com'
        }
        res = json.loads(self.post(self.URL_LOGIN, data))
        if res['code']:
            print 'Login success'

            html = self.get(res['homeUrl'])
            self.getToken(html)
            self.saveCookies()
        else:
            print 'Login failed'
            print res['failDescription']

    def getNotifications(self, start=0, limit=20):
        data = {
            'begin': start,
            'limit': limit,
        }
        res = json.loads(self.get(self.URL_NOTIFICATION, data))
        ntfs = []
        for ntf in res:
            ntfs.append(RenrenNotification(ntf))
        return ntfs

    def removeNotification(self, nid):
        res = self.post('http://notify.renren.com/rmessage/remove?nl=' + nid,
                        self.token)
        print res

    def processNotification(self, nid):
        res = self.post('http://notify.renren.com/rmessage/process?nl=' + nid,
                        self.token)
        print res

    def retrieveStatusComments(self, status, me):
        data = {
            'owner': me,        # current account id
            'source': status,   # comment id
            't': 3,             # type: status
        }
        data = dict(data.items() + self.token.items())
        res = self.post('http://status.renren.com/feedcommentretrieve.do',
                        data)
        print json.loads(res)


def formatNotification(ntf):
    unread = '*' if n.unread else ' '
    desc = n.description if n.type == 'status' else ' '
    return u'{:11} {:1} {:6} {:10} {}'.format(
        n.id, unread, n.type, n.nickname, desc
    )


if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__) or '.')

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s')

    with open('config.json', 'rb') as f:
        config = json.load(f)

    email = config['email']
    password = config['password']

    client = RenrenClient(email, password)

    ntfs = client.getNotifications()
    for n in ntfs:
        print formatNotification(n)

    nid = raw_input('Remove which: ')
    if nid:
        client.removeNotification(nid)

    nid = raw_input('Process which: ')
    if nid:
        client.processNotification(nid)
