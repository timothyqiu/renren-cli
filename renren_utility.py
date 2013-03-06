#!/usr/bin/env python2
# vim:fileencoding=utf-8

"""Utility Module for RenrenCLI
"""

__all__ = [
    'pretty_date',
    'pad_str',
    'html_to_plain_text',
    'get_display_len',
]


import datetime
import re
import unicodedata


def pretty_date(d):
    """Returns a relative date string if possible."""
    # FIXME: Timezone Issue?
    diff = datetime.datetime.now() - d
    if diff.days > 7 or diff.days < 0:
        return d.strftime('%Y-%m-%d')
    elif diff.days == 1:
        return u'1 day ago'
    elif diff.days > 1:
        return u'{} days ago'.format(diff.days)
    elif diff.seconds <= 1:
        return u'just now'
    elif diff.seconds < 60:
        return u'{} seconds ago'.format(diff.seconds)
    elif diff.seconds < 120:
        return u'1 minute ago'
    elif diff.seconds < 3600:
        return u'{} miniutes ago'.format(diff.seconds / 60)
    elif diff.seconds < 7200:
        return u'1 hour ago'
    else:
        return u'{} hours ago'.format(diff.seconds / 3600)


def get_display_len(text):
    """Get display length, considering east asian characters."""
    return sum(
        1 + (unicodedata.east_asian_width(c) in 'WF')
        for c in text
    )


def pad_str(text, width, padchar=' '):
    """Properly pads a string, considering east asian characters."""
    # Not considering ambiguous characters ('A')
    colwidth = get_display_len(text)
    padcount = width - (colwidth if width >= colwidth else 0)
    return u'{}{}'.format(text, padchar * padcount)


def html_to_plain_text(text):
    # Image tags to alt text
    text = re.sub(ur"<img .*?alt=(['\"])([^\1]*?)\1.*?/\s*>", ur"(\2)", text)
    # Remove other tags
    text = re.sub(ur'<.*?>', '', text)
    return text


def test():
    assert pad_str(u'cake', 10, '.') == u'cake......'
    assert pad_str(u'惠山油酥', 10, '.') == u'惠山油酥..'
    assert pad_str(u'おもち', 10, '.') == u'おもち....'
    assert pad_str(u'막걸리', 10, '.') == u'막걸리....'

    assert html_to_plain_text(
        'Click <a href="#">here</a> for <img src="image.png" alt="image"/>.'
    ) == u'Click here for (image).'
    assert html_to_plain_text(
        "<img src='image.png' alt='one'/>.<img src='image.png' alt='two'/>"
    ) == u'(one).(two)'

    print "Don't panic! Everything is fine."


if __name__ == '__main__':
    test()
