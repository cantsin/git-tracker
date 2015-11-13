#!/usr/bin/env python
# pylint: disable=C0103,C0111,W0142

# ugh. work around an internal bug with flask and python3.4
import pkgutil
old_loader = pkgutil.get_loader
def override_loader(*args, **kwargs):
    try:
        return old_loader(*args, **kwargs)
    except AttributeError:
        return None
pkgutil.get_loader = override_loader

from flask import Flask, request, jsonify, make_response
from flask.ext.login import LoginManager, login_required, login_user, \
    logout_user, current_user
from flask.ext.cors import CORS
from werkzeug import secure_filename
from werkzeug.exceptions import HTTPException, default_exceptions

from util import get_gravatar, slugify, save_uploaded_file
from models import init_db, User, Tag
from git import GitOperations, GitException
from data import DataOperations
from cron import scheduler

from functools import wraps
import io, csv
import os

UPLOAD_FOLDER = 'uploads'

# prevent werkzeug from emitting HTML errors.
def make_json_app(import_name, **kwargs):
    def make_json_error(ex):
        response = jsonify(success=False, error=str(ex))
        response.status_code = (ex.code if isinstance(ex, HTTPException) else 500)
        return response

    app = Flask(import_name, **kwargs)
    CORS(app)

    for code in default_exceptions.keys():
        app.error_handler_spec[None][code] = make_json_error

    return app

app = make_json_app('git-tracker')

login_manager = LoginManager()
login_manager.init_app(app)

def success(result=None):
    if not result:
        return jsonify(success=True)
    return jsonify(success=True, data=result)

def failure(error):
    return jsonify(success=False, errors=[error])

def jsoncheck(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            r = func(*args, **kwargs)
            return r
        except KeyError as e:
            return failure(str(''.join(e.args)) + ' not found')
        except IndexError as e:
            return failure('Error: ' + str(e.args))
        except TypeError as e:
            return failure('Error: ' + str(e.args))
    return wrapper

@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)

@app.route('/login', methods=['POST'])
@jsoncheck
def login():
    request.get_json(force=True)
    email = request.json['email']
    password = request.json['password']
    user = User.query.filter_by(login=email).scalar()
    if user and user.check_password(password):
        login_user(user)
        return success()
    return failure('Email and password do not match.')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return success()

@app.route('/users', methods=['POST'])
@jsoncheck
def add_user():
    request.get_json(force=True)
    email = request.json['email']
    if not '@' in email:
        return failure('Please provide a proper email.')
    password1 = request.json['password']
    password2 = request.json['password2']
    if password1 != password2:
        return failure('Passwords do not match.')
    new_user = User(email, password1)
    new_user.avatar_image = get_gravatar(email)
    new_user.save() # generate an id for this user
    new_user.add_emails(email)
    return success()

@app.route('/users/keys', methods=['POST'])
@login_required
def update_keys():
    try:
        public_key = request.files['public-key']
        if public_key.filename:
            current_user.ssh_public_key_path = save_uploaded_file(current_user, public_key, UPLOAD_FOLDER)
            current_user.save()
        private_key = request.files['private-key']
        if private_key.filename:
            current_user.ssh_private_key_path = save_uploaded_file(current_user, private_key, UPLOAD_FOLDER)
            current_user.save()
        return success()
    except KeyError:
        return failure('Please fill out all fields.')

@app.route('/emails', methods=['POST'])
@jsoncheck
@login_required
def add_user_email():
    email = request.json['email']
    if not '@' in email:
        return failure('Please provide a proper email.')
    if current_user.emails.filter_by(email=email).scalar():
        return failure('Current email already exists.')
    current_user.add_emails(email)
    return success()

@app.route('/emails/<id>', methods=['DELETE'])
@login_required
def delete_user_email(id):
    ue = current_user.emails.filter_by(id=id).first_or_404()
    ue.delete()
    return success()

@app.route('/repositories', methods=['POST'])
@jsoncheck
@login_required
def add_repository():
    try:
        location = request.json['location']
        if current_user.repositories.filter_by(location=location).scalar():
            return failure('Given repository already exists.')
        repository = GitOperations.create_repository(current_user, location)
        repository.save()
        repository.update_commit_info()
        return success()
    except GitException as ge:
        return failure(ge.args[0][0])

@app.route('/repositories/<id>', methods=['GET'])
@login_required
def view_repository(id):
    repository = current_user.repositories.filter_by(id=id).first_or_404()
    identifier = repository.get_shorthand_of_branch('master')
    sha1 = repository.get_sha1_of_branch('master')
    tags = current_user.tags.order_by('name').all()
    result= {'kind': repository.kind,
             'name': repository.get_name(),
             'start': repository.get_first_updated(),
             'end': repository.get_last_updated(),
             'updated': repository.updated_at,
             'git_identifier': identifier,
             'git_sha1': sha1,
             'tags': tags}
    return success(result=result)

@app.route('/repositories/<id>', methods=['DELETE'])
@login_required
def delete_repository(id):
    repository = current_user.repositories.filter_by(id=id).first_or_404()
    repository.clear_tags()
    repository.delete()
    return success()

@app.route('/repositories/<id>/activity', methods=['GET'])
@login_required
def repository_activity(id):
    repository = current_user.repositories.filter_by(id=id).first_or_404()
    start = request.args.get('start') or repository.get_first_updated()
    end = request.args.get('end') or repository.get_last_updated()
    result = repository.histogram(int(start), int(end))
    return success(result=result)

@app.route('/repositories/<id>/refresh', methods=['GET'])
@login_required
def refresh_repository(id):
    repository = current_user.repositories.filter_by(id=id).first_or_404()
    repository.refresh()
    repository.update_commit_info()
    repository.save()
    return success()

@app.route('/repositories/dump', methods=['GET'])
@login_required
def dump_repositories():
    si = io.StringIO()
    fake_csv = csv.writer(si)
    for repository in current_user.repositories.all():
        tags = ','.join([tag.name for tag in repository.tags])
        fake_csv.writerow([repository.get_name(), repository.location, repository.kind, tags])
    response = make_response(si.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=repositories.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

@app.route('/repositories/load', methods=['POST'])
@login_required
def load_repositories():
    csv_file = request.files['bulk-upload']
    if not csv_file.filename:
        return failure('No file uploaded.')
    csv_path = save_uploaded_file(current_user, csv_file, UPLOAD_FOLDER)
    fake_csv = csv.reader(open(csv_path, 'r+'))
    for line in fake_csv:
        [_, location, _, tags] = line
        # create the repository if not already extant.
        has_repository = current_user.repositories.filter_by(location=location)
        if not has_repository.all():
            repository = GitOperations.create_repository(current_user, location)
            repository.save()
            repository.update_commit_info()
        else:
            repository = has_repository.first()
        # apply tags if not already extant.
        for tag_name in tags.split(','):
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            has_tag = current_user.tags.filter_by(name=tag_name)
            tag = has_tag.first() if has_tag.all() else Tag(current_user, tag_name).save()
            if repository.tags.count(tag) == 0:
                repository.tags.append(tag)
    return success()

@app.route('/repositories/<id>/apply', methods=['POST'])
@login_required
def apply_tags(id):
    repository = current_user.repositories.filter_by(id=id).first_or_404()
    tag_names = [key for (key, value) in request.json.items()
                 if key.startswith('apply-') and value == 'on']
    repository.clear_tags()
    for tag_name in tag_names:
        tag = current_user.tags.filter_by(slug=tag_name[6:]).first_or_404()
        repository.tags.append(tag)
    repository.save()
    return success()

@app.route('/tags', methods=['POST'])
@jsoncheck
@login_required
def add_tag():
    name = request.json['name'].strip()
    if name == '':
        return failure('Tag cannot be blank.')
    if current_user.tags.filter_by(name=name).scalar():
        return failure('Given tag name already exists.')
    if current_user.tags.filter_by(slug=slugify(name)).scalar():
        return failure('Given tag slug already exists.')
    tag = Tag(current_user, name).save()
    return success()

@app.route('/tags/<id>', methods=['DELETE'])
@login_required
def delete_tag(id):
    tag = current_user.tags.filter_by(id=id).first_or_404()
    tag.delete()
    return success()

@app.route('/tags/<id>', methods=['GET'])
@login_required
def view_tag(id):
    tag = current_user.tags.filter_by(id=id).first_or_404()
    first_updated = DataOperations.get_first_updated(tag.repositories)
    last_updated = DataOperations.get_last_updated(tag.repositories)
    result = {'tag': tag,
              'name': tag.name,
              'first_updated': first_updated,
              'last_updated': last_updated}
    return success(result=result)

@app.route('/tags/<id>/activity', methods=['GET'])
@login_required
def tag_activity(id):
    tag = current_user.tags.filter_by(id=id).first_or_404()
    first_updated = DataOperations.get_first_updated(tag.repositories)
    last_updated = DataOperations.get_last_updated(tag.repositories)
    start = int(request.args.get('start')) or first_updated
    end = int(request.args.get('end')) or last_updated
    result = DataOperations.histogram(tag.repositories, start, end)
    return success(result=result)

@app.route('/dashboard')
@login_required
def dashboard():
    first_updated = DataOperations.get_first_updated(current_user.repositories)
    last_updated = DataOperations.get_last_updated(current_user.repositories)
    result = {'first_updated': first_updated,
              'last_updated': last_updated}
    return success(result=result)

@app.route('/dashboard/activity')
@login_required
def all_activity():
    first_updated = DataOperations.get_first_updated(current_user.repositories)
    last_updated = DataOperations.get_last_updated(current_user.repositories)
    start = int(request.args.get('start')) or first_updated
    end = int(request.args.get('end')) or last_updated
    result = DataOperations.histogram(current_user.repositories, start, end)
    return success(result=result)

if __name__ == '__main__':
    try:
        import config
        app.secret_key = config.secret_key
    except ImportError:
        import os
        app.secret_key = os.urandom(24)
    import sys
    app.debug = True
    app.config['version'] = "1.0"
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    init_db()
    scheduler.start()
    port = 5000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    app.run(host='0.0.0.0', port=port)
