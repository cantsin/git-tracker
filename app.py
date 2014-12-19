#!/usr/bin/env python

from flask import Flask, render_template, request, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, login_required, login_user, logout_user
from util import slugify, naturaltime, clone_bare_repository
from models import User, Repository, Tag
from git import GitException

app = Flask('git-tracker')
app.jinja_env.filters['slugify'] = slugify
app.jinja_env.filters['naturaltime'] = naturaltime

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', error=error), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).scalar()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('all'))
        else:
            error = 'Email and password do not match.'
    return render_template('index.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/repository/<name>')
@login_required
def view_repository(name):
    repository = Repository.query.filter_by(name=name).first_or_404()
    identifier = repository.get_shorthand_of_branch('master')
    sha1 = repository.get_sha1_of_branch('master')
    kwargs = { 'repository': repository,
               'current_selection': repository.name,
               'git_identifier': identifier,
               'git_sha1': sha1,
               'selection': 'repositories' }
    return render_template('view_repository.html', **kwargs)

@app.route('/repositories/add')
@login_required
def add_repository():
    try:
        location = request.form['location']
        repository = clone_bare_repository(current_user, location)
        url = url_for('view_repository', name=repository.name)
        return flask.jsonify(success=url)
    # TODO: Check for pre-existing
    except GitException as e:
        return flask.jsonify(error=e)
    except IndexError:
        return flask.jsonify(error='Location is invalid.')

@app.route('/tag/<slug>')
@login_required
def view_tag(slug):
    tag = Tag.query.filter_by(slug=slug).first_or_404()
    kwargs = { 'tag': tag,
               'current_selection': tag.name,
               'selection': 'tags' }
    return render_template('view_tag.html', **kwargs)

@app.route('/tags/add')
@login_required
def add_tag():
    try:
        name = request.form['name']
        tag = Tag(current_user, name).save()
        url = url_for('view_tag', slug=tag.slug)
        return flask.jsonify(success=url)
    # TODO: Check for pre-existing
    except IndexError:
        return flask.jsonify(error='Name field is invalid.')

@app.route('/all')
@login_required
def all():
    kwargs = { 'selection': 'repositories' }
    return render_template('all.html', **kwargs)

@app.route('/<path:path>')
def static_proxy(path):
  return app.send_static_file(path)

if __name__ == '__main__':
    try:
        import config
        app.secret_key = config.secret_key
    except ImportError:
        import os
        app.secret_key = os.urandom(24)
    app.debug = True
    app.run()
