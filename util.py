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
