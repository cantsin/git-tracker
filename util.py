# pylint: disable=C0103,C0111

from unicodedata import normalize
from datetime import datetime
from flask import request, url_for
from werkzeug import secure_filename

import urllib.parse
import hashlib
import humanize
import re
import os

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def slugify(text, delim=b'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return delim.join(result).decode("utf-8", "strict")

def get_gravatar(email):
    size = 69
    base_url = 'http://www.gravatar.com/avatar/'
    url = base_url + hashlib.md5(email.lower().encode('utf8')).hexdigest() + "?"
    url += urllib.parse.urlencode({'d': 'identicon', 's': str(size)})
    return url

def save_uploaded_file(user, request_file, where):
    prefix = os.path.join(where, str(user.id))
    os.makedirs(prefix, exist_ok=True)
    path = os.path.join(prefix, secure_filename(request_file.filename))
    request_file.save(path)
    return path
