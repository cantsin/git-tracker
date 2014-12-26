# pylint: disable=C0103,C0111

from unicodedata import normalize
from datetime import datetime

import humanize
import re

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def slugify(text, delim=b'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return delim.join(result).decode("utf-8", "strict")

def naturaltime(ue):
    return humanize.naturaltime(datetime.fromtimestamp(ue))
