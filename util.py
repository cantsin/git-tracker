# pylint: disable=C0103,C0111

from unicodedata import normalize
from datetime import datetime
from flask import request, url_for

import urllib.parse
import hashlib
import humanize
import re

def get_gravatar(email):
    size = 69
    base_url = 'http://www.gravatar.com/avatar/'
    url = base_url + hashlib.md5(email.lower().encode('utf8')).hexdigest() + "?"
    url += urllib.parse.urlencode({'d': 'identicon', 's': str(size)})
    return url

def is_safe_url(target):
    ref_url = urllib.parse.urlparse(request.host_url)
    parsed_url = urllib.parse.urljoin(request.host_url, target)
    test_url = urllib.parse.urlparse(parsed_url)
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc
