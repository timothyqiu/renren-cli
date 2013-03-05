#!/usr/bin/env python2
# vim:fileencoding=utf-8

from datetime import datetime
import cookielib
import os
import re
import logging
import json
import sys
import urllib
import urllib2

from renren_encryptor import LoginEncryptor


class RenrenNotification:

    def __init__(self, data):
        self.parse(data)

    def parse(self, ntf):
        timestamp = int(ntf['time'])
        content = ntf['content']
        links = re.findall(r'<a.*?href="https?://(.*?)\..*?".*?>(.*?)</a>', content)

        self.id = ntf['nid']
        self.unread = int(ntf['unread']) > 0
        self.time = datetime.fromtimestamp(timestamp)
        self.removeCallback = ntf['rmessagecallback']
        self.processCallback = ntf['processcallback']
        self.nickname = links[0][1]
        self.type = links[1][0]
        self.description = links[1][1]

        if self.type == 'status':
            m = re.search(r'http://status.renren.com/getdoing.do\?id=(\d+)&doingId=(\d+)', content)
            assert m, content
            self.owner_id = m.group(1)
            self.status_id = m.group(2)


class RenrenStatus:

    def __init__(self, raw):
        self.parse(raw)


    def parse(self, raw):
        self.content = raw['content']
        self.time = datetime.strptime(raw['dtime'], '%Y-%m-%d %H:%M:%S')
        self.owner = {'id': raw['userId'], 'name': raw['name']}
        self.id = raw['id']
        self.comment_count = int(raw['comment_count'])

        # Forward
        self.root = {}
        if 'rootDoingId' in raw:
            self.root = {
                'status_id': raw['rootDoingId'],
                'owner': {
                    'id': raw['rootDoingUserId'],
                    'name': raw['rootDoingUserName'],
                },
                'content': raw['rootContent'],
            }


class RenrenStatusSheet:

    def __init__(self, data=None):
        # `data` can be None because empty sheet is meaningful
        self.total = 0
        self.status = []
        if data:
            self.parse(data)

    def __unicode__(self):
        desc = [
            u'Status Sheet (count:{:d}  total:{:d})'.format(
                len(self.status), self.total
            )
        ]
        desc.extend([unicode(s) for s in self.status])
        return u'\n\n'.join(desc)

    def parse(self, res):
        self.total = int(res['count'])
        self.status = [RenrenStatus(entry) for entry in res['doingArray']]


class Client:

    URL_CAPTCHA = \
        'http://icode.renren.com/getcode.do?t=web_login&rnd=Math.random()'
    URL_SHOW_CAPTCHA = 'http://www.renren.com/ajax/ShowCaptcha'
    URL_LOGIN = 'http://www.renren.com/ajaxLogin/login'
    URL_NOTIFICATION = \
        'http://notify.renren.com/rmessage/get?getbybigtype=1&bigtype=1&view=16'

    DEFAULT_COOKIES_FILENAME = '.renren.cookies'
    DEFAULT_TOKEN_URL = 'http://i.renren.com/store/view/home'

    def __init__(self):
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
        check_match = re.search(r"get_check:'([^']+)'", html)
        check_x_match = re.search(r"get_check_x:'([^']+)'", html)
        if check_match and check_x_match:
            self.token['requestToken'] = check_match.group(1)
            self.token['_rtk'] = check_x_match.group(1)
            logging.info('Token got from %s' % url)
        else:
            logging.warn('Token not found in %s' % url)

    def is_logged_in(self):
        return bool(self.token)

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

    def get_icode(self, email):
        show = self.post(self.URL_SHOW_CAPTCHA, {'email': email})
        if show == '0':
            return ''
        return self.get_captcha()

    def get_captcha(self):
        captcha = self.get(self.URL_CAPTCHA)
        with open('captcha.jpg', 'wb') as image:
            image.write(captcha)
        print 'Captcha image saved to captcha.jpg'
        return raw_input('Captcha: ')

    def login(self, email, password):
        query = {
            'email': email,
            'password': self.encryptor.encrypt(password),
            'rkey': self.encryptor.key['rkey'],
            'icode': self.get_icode(email),
            'captcha_type': 'web_login',
        }
        res = json.loads(self.post(self.URL_LOGIN, query))
        if res['code']:
            logging.info('Login success.')
            self.retrieve_token(res['homeUrl'])
            return True, None
        else:
            logging.error('Login failed: %s', res['failDescription'])
            return False, res['failDescription']

    def get_notifications(self, page=1, page_size=20):
        if not self.is_logged_in():
            return None, 'You are not logged in'

        query = {
            'begin': page_size * (page - 1),
            'limit': page_size,
        }
        res = json.loads(self.get(self.URL_NOTIFICATION, query))
        return [RenrenNotification(ntf) for ntf in res], None

    def remove_notification(self, nid):
        self.post('http://notify.renren.com/rmessage/remove?nl=' + nid,
                  self.token)

    def process_notification(self, nid):
        self.post('http://notify.renren.com/rmessage/process?nl=' + nid,
                  self.token)

    def get_status(self, owner=None, page=1, page_size=5):
        if not self.is_logged_in():
            return None, 'You are not logged in'

        # Calculate the actual pages for request
        # 20 status are returned each time
        # FIXME: find a way to alter page size in request?
        begin = page_size * (page - 1)
        end = begin + page_size
        req_page_size = 20
        page_begin = begin / req_page_size
        page_end = end / req_page_size
        req_pages = range(page_begin, page_end + 1)

        # Basic request setup
        if not owner:
            send_request = lambda p: self.get(
                'http://status.renren.com/GetFriendDoing.do',
                {'curpage': p}
            )
        else:
            send_request = lambda p: self.get(
                'http://status.renren.com/GetSomeomeDoingList.do',
                {'curpage': p, 'userId': owner}
            )

        res = map(send_request, req_pages)    # Response
        raw = map(json.loads, res)            # Dict
        sheets = map(RenrenStatusSheet, raw)  # Dict to objects

        # Combine all returned pages
        res_sheet = RenrenStatusSheet()
        res_sheet.total = sheets[0].total
        res_sheet.status = [
            s
            for sheet in sheets
            for s in sheet.status
        ]

        # Cut to what we want
        response_count = len(res_sheet.status)

        offset = begin % req_page_size
        length = page_size if page_size <= response_count else response_count
        res_sheet.status = res_sheet.status[offset:offset+length]

        return res_sheet, None

    def retrieve_status_comments(self, status, owner):
        query = {
            'owner': owner,     # status owner id
            'source': status,   # status id
            't': 3,             # type: status
        }
        query = dict(query.items() + self.token.items())
        res = self.post('http://status.renren.com/feedcommentretrieve.do',
                        query)

        res = json.loads(res)
        success = res['code']

        status_owner = res['ownerid']
        print 'Status owner: %s' % status_owner
        for comment in res['replyList']:
            comment_id = comment['id']
            nickname = comment['ubname']
            content = comment['replyContent']
            owner = comment['ownerId']
            print comment_id, nickname, content


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')
