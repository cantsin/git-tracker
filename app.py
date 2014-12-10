#!/usr/bin/env python

from flask import Flask, render_template

app = Flask(__name__)

# sample information, for now.
data = { 'repositories': ['fsharp-finger-trees',
                          'glc-client',
                          'dotemacs',
                          'sovereign',
                          'pcgen-rules',
                          'ergodox-firmware',
                          'rust'],
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
    return render_template('404.html'), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logout')
def logout():
    pass

@app.route('/repository/<name>')
def view_repository(name):
    kwargs = { 'name': name,
               'git_identifier': 'master',
               'git_sha1': '523b75f3',
               'current_selection': 'fsharp-finger-trees',
               'expanded_selection': 'master',
               'branches': ['master', 'monoids', 'v1.0'],
               'selection': 'repositories' }
    kwargs.update(data)
    return render_template('view_repository.html', **kwargs)

@app.route('/tag/<name>')
def view_tag(name):
    return render_template('view_tag.html')

@app.route('/all')
def all():
    return render_template('all.html')

@app.route('/<path:path>')
def static_proxy(path):
  return app.send_static_file(path)

if __name__ == '__main__':
    app.debug = True
    app.run()
