#!/usr/bin/env python

from flask import Flask, render_template, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from util import slugify
from models import User, Repository, Tag
import pygit2

app = Flask("git-tracker")
app.jinja_env.filters['slugify'] = slugify

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
    repository = Repository.query.filter_by(name=name).first_or_404()
    user = User.query.first() # placeholder until we have login

    ondisk = pygit2.Repository('repositories/' + repository.name)
    branches = ondisk.listall_branches(pygit2.GIT_BRANCH_REMOTE)
    main_branch = ondisk.lookup_branch('master')
    sha1 = str(main_branch.get_object().id)

    kwargs = { 'user': user,
               'repository': repository,
               'branches': branches,
               'current_selection': repository.name,
               'expanded_selection': main_branch.shorthand,
               'git_identifier': main_branch.shorthand,
               'git_sha1': sha1[:6],
               'selection': 'repositories' }
    return render_template('view_repository.html', **kwargs)

@app.route('/tag/<slug>')
def view_tag(slug):
    tag = Tag.query.filter_by(slug=slug).first_or_404()
    user = User.query.first() # placeholder until we have login
    kwargs = { 'user': user,
               'tag': tag,
               'current_selection': tag.name,
               'selection': 'tags' }
    return render_template('view_tag.html', **kwargs)

@app.route('/all')
def all():
    user = User.query.first() # placeholder until we have login
    kwargs = { 'user': user,
               'selection': 'repositories' }
    return render_template('all.html', **kwargs)

@app.route('/<path:path>')
def static_proxy(path):
  return app.send_static_file(path)

if __name__ == '__main__':
    app.debug = True
    app.run()
