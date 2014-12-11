#!/usr/bin/env python

from flask import Flask, render_template, redirect, url_for
from unicodedata import normalize

import re

app = Flask(__name__)

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

@app.template_filter()
def slugify(text, delim=b'-'):
    """Generates an slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return delim.join(result).decode("utf-8", "strict")

app.jinja_env.filters['slugify'] = slugify

# sample information, for now.
data = { 'repositories': [('fsharp-finger-trees', ['master', 'monoids', 'v1.0']),
                          ('glc-client', []),
                          ('dotemacs', []),
                          ('sovereign', []),
                          ('pcgen-rules', []),
                          ('ergodox-firmware', []),
                          ('rust', [])],
         'tags': [('F#', 2),
                  ('Data Structures', 3),
                  ('Completed', 1),
                  ('Public', 7),
                  ('Github', 7),
                  ('Code', 10),
                  ('Rust', 1),
                  ('Lua', 3),
                  ('Hack Day', 4),
                  ('Abandoned', 0),
                  ('Private', 3),
                  ('All', 42)],
         'avatar_image': 'https://avatars2.githubusercontent.com/u/3013175?v=3&s=460' }

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', error=error), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return redirect(url_for('all'))

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/repository/<name>')
def view_repository(name):
    repository_list = map(lambda x: x[0], data['repositories'])
    if not name in repository_list:
        return page_not_found("No such repository found.")
    kwargs = { 'name': name,
               'git_identifier': 'master',
               'git_sha1': '523b75f3',
               'repository_tags': ['Completed', 'F#', 'Public', 'Github', 'Code'],
               'current_selection': 'fsharp-finger-trees',
               'expanded_selection': 'master',
               'selection': 'repositories' }
    kwargs.update(data)
    return render_template('view_repository.html', **kwargs)

@app.route('/tag/<name>')
def view_tag(name):
    kwargs = { 'name': name,
               'number': 7,
               'current_selection': 'Data Structures',
               'selection': 'tags' }
    kwargs.update(data)
    return render_template('view_tag.html', **kwargs)

@app.route('/all')
def all():
    kwargs = { 'selection': 'repositories' }
    kwargs.update(data)
    return render_template('all.html', **kwargs)

@app.route('/<path:path>')
def static_proxy(path):
  return app.send_static_file(path)

if __name__ == '__main__':
    app.debug = True
    app.run()
