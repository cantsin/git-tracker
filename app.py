#!/usr/bin/env python3.4
# pylint: disable=C0103,C0111,W0142

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user
from werkzeug import secure_filename
from util import slugify, naturaltime, get_gravatar, url_for_redirect_back
from models import User, Tag
from git import GitOperations, GitException
from data import DataOperations

import os

UPLOAD_FOLDER = 'uploads'

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
        user = User.query.filter_by(login=email).scalar()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            error = 'Email and password do not match.'
    return render_template('index.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# helper function.
def save_uploaded_file(user, request_file):
    prefix = os.path.join(app.config['UPLOAD_FOLDER'], str(user.id))
    os.makedirs(prefix, exist_ok=True)
    path = os.path.join(prefix, secure_filename(request_file.filename))
    request_file.save(path)
    return path

@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        email = request.form['email']
        if not '@' in email:
            error = 'Please provide a proper email.'
            return render_template('user_form.html', error=error)
        password1 = request.form['password']
        password2 = request.form['password2']
        if password1 != password2:
            error = 'Passwords do not match.'
            return render_template('user_form.html', error=error)
        public_key = request.files['public-key']
        if not public_key.filename:
            error = 'No public key provided.'
            return render_template('user_form.html', error=error)
        private_key = request.files['private-key']
        if not private_key.filename:
            error = 'No private key provided.'
            return render_template('user_form.html', error=error)
        new_user = User(email, password1)
        new_user.avatar_image = get_gravatar(email)
        new_user.save() # generate an id for this user
        new_user.ssh_public_key_path = save_uploaded_file(new_user, public_key)
        new_user.ssh_private_key_path = save_uploaded_file(new_user, private_key)
        new_user.save()
        new_user.add_emails(email)
        return redirect(url_for('login'))
    return render_template('user_form.html')

@app.route('/users/keys', methods=['POST'])
@login_required
def update_keys():
    try:
        public_key = request.files['public-key']
        if public_key.filename:
            current_user.ssh_public_key_path = save_uploaded_file(current_user, public_key)
            current_user.save()
        private_key = request.files['private-key']
        if private_key.filename:
            current_user.ssh_private_key_path = save_uploaded_file(current_user, private_key)
            current_user.save()
        url = url_for_redirect_back('dashboard')
        return redirect(url)
    except KeyError:
        return jsonify(error='Please fill out all fields.')

@app.route('/users/email/add', methods=['POST'])
@login_required
def add_user_email():
    try:
        email = request.form['email']
        if not '@' in email:
            return jsonify(error='Please provide a proper email.')
        if current_user.emails.filter_by(email=email).scalar():
            return jsonify(error='Current email already exists.')
        current_user.add_emails(email)
        url = url_for_redirect_back('dashboard')
        return jsonify(success=url)
    except IndexError:
        return jsonify(error='Please fill out all fields.')

@app.route('/users/email/<useremail_id>/delete', methods=['GET'])
@login_required
def delete_user_email(useremail_id):
    ue = current_user.emails.filter_by(id=useremail_id).first_or_404()
    ue.delete()
    url = url_for('dashboard')
    return jsonify(success=url)

@app.route('/repository/<name>')
@login_required
def view_repository(name):
    repository = current_user.repositories.filter_by(name=name).first_or_404()
    identifier = repository.get_shorthand_of_branch('master')
    sha1 = repository.get_sha1_of_branch('master')
    tags = current_user.tags.order_by('name')
    kwargs = {'repository': repository,
              'current_selection': repository.name,
              'git_identifier': identifier,
              'git_sha1': sha1,
              'tags': tags,
              'selection': 'repositories'}
    return render_template('view_repository.html', **kwargs)

@app.route('/repositories/<name>/activity/', methods=['GET'])
@login_required
def repository_activity(name):
    repository = current_user.repositories.filter_by(name=name).first_or_404()
    start = int(request.args.get('start')) or repository.get_first_updated()
    end = int(request.args.get('end')) or repository.get_last_updated()
    return jsonify({'result': repository.histogram(start, end)})

@app.route('/repositories/<name>/delete', methods=['GET'])
@login_required
def delete_repository(name):
    repository = current_user.repositories.filter_by(name=name).first_or_404()
    repository.clear_tags()
    repository.delete()
    return redirect(url_for('dashboard'))

@app.route('/repositories/<name>/refresh', methods=['GET'])
@login_required
def refresh_repository(name):
    repository = current_user.repositories.filter_by(name=name).first_or_404()
    repository.refresh()
    repository.save()
    url = url_for('view_repository', name=repository.name)
    return jsonify(success=url)

@app.route('/repositories/add', methods=['POST'])
@login_required
def add_repository():
    try:
        location = request.form['location']
        if current_user.repositories.filter_by(location=location).scalar():
            return jsonify(error='Given repository already exists.')
        repository = GitOperations.create_repository(current_user, location)
        url = url_for('view_repository', name=repository.name)
        return jsonify(success=url)
    except GitException as ge:
        return jsonify(error=ge.args)
    except IndexError:
        return jsonify(error='Location is invalid.')

@app.route('/repository/<repository_name>/tags/apply', methods=['POST'])
@login_required
def apply_tags(repository_name):
    repository = current_user.repositories.filter_by(name=repository_name).first_or_404()
    tag_names = [key for (key, value) in request.form.items()
                 if key.startswith('apply-') and value == 'on']
    repository.clear_tags()
    for tag_name in tag_names:
        tag = current_user.tags.filter_by(slug=tag_name[6:]).first_or_404()
        repository.tags.append(tag)
    repository.save()
    url = url_for('view_repository', name=repository_name)
    return jsonify(success=url)

@app.route('/tag/<slug>')
@login_required
def view_tag(slug):
    tag = current_user.tags.filter_by(slug=slug).first_or_404()
    first_updated = DataOperations.get_first_updated(tag.repositories)
    last_updated = DataOperations.get_last_updated(tag.repositories)
    kwargs = {'tag': tag,
              'current_selection': tag.name,
              'first_updated': first_updated,
              'last_updated': last_updated,
              'selection': 'tags'}
    return render_template('view_tag.html', **kwargs)

@app.route('/tags/<slug>/activity/', methods=['GET'])
@login_required
def tag_activity(slug):
    tag = current_user.tags.filter_by(slug=slug).first_or_404()
    first_updated = DataOperations.get_first_updated(tag.repositories)
    last_updated = DataOperations.get_last_updated(tag.repositories)
    start = int(request.args.get('start')) or first_updated
    end = int(request.args.get('end')) or last_updated
    result = DataOperations.histogram(tag.repositories, start, end)
    return jsonify({'result': result})

@app.route('/tags/<slug>/delete', methods=['GET'])
@login_required
def delete_tag(slug):
    tag = current_user.tags.filter_by(slug=slug).first_or_404()
    tag.delete()
    return redirect(url_for('dashboard'))

@app.route('/tags/add', methods=['POST'])
@login_required
def add_tag():
    try:
        name = request.form['name'].strip()
        if name == '':
            return jsonify(error='Tag cannot be blank.')
        if current_user.tags.filter_by(name=name).scalar():
            return jsonify(error='Given tag name already exists.')
        if current_user.tags.filter_by(slug=slugify(name)).scalar():
            return jsonify(error='Given tag slug already exists.')
        tag = Tag(current_user, name).save()
        url = url_for('view_tag', slug=tag.slug)
        return jsonify(success=url)
    except IndexError:
        return jsonify(error='Name field is invalid.')

@app.route('/dashboard/activity')
@login_required
def all_activity():
    first_updated = DataOperations.get_first_updated(current_user.repositories)
    last_updated = DataOperations.get_last_updated(current_user.repositories)
    start = int(request.args.get('start')) or first_updated
    end = int(request.args.get('end')) or last_updated
    result = DataOperations.histogram(current_user.repositories, start, end)
    return jsonify({'result': result})

@app.route('/dashboard')
@login_required
def dashboard():
    first_updated = DataOperations.get_first_updated(current_user.repositories)
    last_updated = DataOperations.get_last_updated(current_user.repositories)
    kwargs = {'first_updated': first_updated,
              'last_updated': last_updated,
              'selection': 'repositories'}
    return render_template('dashboard.html', **kwargs)

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
    app.config['version'] = "1.0"
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.run()
