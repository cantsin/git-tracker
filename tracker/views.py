#!/usr/bin/env python
# pylint: disable=C0103,C0111,W0142

from flask import Flask, request, jsonify, make_response
from flask.ext.login import login_required, login_user, logout_user, current_user

from .util import get_gravatar, slugify, save_uploaded_file
from .models import User, Tag
from .git import GitOperations, GitException
from .data import DataOperations
from tracker import app

from functools import wraps
import io, csv

def success(result=None):
    if not result:
        return jsonify(success=True)
    return jsonify(success=True, data=result)

def failure(error, code=None):
    response = jsonify(success=False, errors=[error])
    response.status_code = code or 422
    return response

def jsoncheck(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            r = func(*args, **kwargs)
            return r
        except KeyError as e:
            return failure(str(''.join(e.args)) + ' not found', code=400)
    return wrapper

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

@app.route('/users', methods=['PUT'])
@login_required
def update_keys():
    try:
        upload = app.config['UPLOAD_FOLDER']
        public_key = request.files['public-key']
        if public_key.filename:
            current_user.ssh_public_key_path = save_uploaded_file(current_user, public_key, upload)
            current_user.save()
        private_key = request.files['private-key']
        if private_key.filename:
            current_user.ssh_private_key_path = save_uploaded_file(current_user, private_key, upload)
            current_user.save()
        return success()
    except KeyError:
        return failure('Please fill out all fields.')

@app.route('/emails', methods=['GET'])
@login_required
def get_emails():
    data = [dict(id=e.id,
                 email=e.email)
            for e in current_user.emails.all()]
    return success(result=data)

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

@app.route('/repositories', methods=['GET'])
@login_required
def get_repositories():
    data = [dict(id=r.id,
                 name=r.name,
                 kind=r.kind)
            for r in current_user.repositories.all()]
    return success(result=data)

@app.route('/repositories', methods=['POST'])
@jsoncheck
@login_required
def add_repository():
    try:
        location = request.json['location']
        _, name = GitOperations.git_uri_parse(location)
        if current_user.repositories.filter_by(name=name).scalar():
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
    first_updated = repository.get_first_updated()
    last_updated = repository.get_last_updated()
    start = int(request.args.get('start', first_updated))
    end = int(request.args.get('end', last_updated))
    histogram = repository.histogram(start, end)
    reference_count = request.args.get('reference_count')
    reference_count = int(reference_count) if reference_count else None
    references = [ref for ref in repository.get_latest_refs(count=reference_count)]
    commit_count = request.args.get('commit_count')
    commit_count = int(commit_count) if commit_count else None
    commits = []
    for commit in repository.get_commits(count=commit_count):
        changed_files, additions, deletions = repository.get_numstat(commit)
        commits.append(dict(commit_time=commit.commit_time,
                            author_name=commit.author.name,
                            message=commit.message,
                            changed_files=changed_files,
                            additions=additions,
                            deletions=deletions))
    commit_count = repository.get_commit_count()
    author_count = repository.get_author_count()
    file_count = repository.get_file_count()
    line_count = repository.get_line_count()
    identifier = repository.get_shorthand_of_branch('master')
    sha1 = repository.get_sha1_of_branch('master')
    tags = current_user.tags.order_by('name').all()
    result= {'kind': repository.kind,
             'name': repository.name,
             'first_updated': first_updated,
             'last_updated': last_updated,
             'histogram': histogram,
             'updated': repository.updated_at,
             'git_identifier': identifier,
             'git_sha1': sha1,
             'references': references,
             'commits': commits,
             'commit_count': commit_count,
             'author_count': author_count,
             'file_count': file_count,
             'line_count': line_count,
             'tags': tags}
    return success(result=result)

@app.route('/repositories/<id>', methods=['PUT'])
@jsoncheck
@login_required
def apply_tags(id):
    repository = current_user.repositories.filter_by(id=id).first_or_404()
    tag_ids = request.json['ids']
    repository.clear_tags()
    for tag_id in tag_ids:
        tag = current_user.tags.filter_by(id=tag_id).first_or_404()
        repository.tags.append(tag)
    repository.save()
    return success()

@app.route('/repositories/<id>', methods=['DELETE'])
@login_required
def delete_repository(id):
    repository = current_user.repositories.filter_by(id=id).first_or_404()
    repository.clear_tags()
    repository.delete()
    return success()

@app.route('/tags', methods=['GET'])
@login_required
def get_tags():
    data = [dict(id=t.id,
                 name=t.name,
                 slug=t.slug)
            for t in current_user.tags.all()]
    return success(result=data)

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

@app.route('/tags/<id>', methods=['GET'])
@login_required
def view_tag(id):
    start = request.args.get('start', None)
    end = request.args.get('end', None)
    tag = current_user.tags.filter_by(id=id).first_or_404()
    ops = DataOperations(tag.repositories, start=start, end=end)
    result = {'repositories': [repo.id for repo in tag.repositories],
              'repository_count': tag.repositories.count(),
              'slug': tag.slug,
              'name': tag.name,
              'id': tag.id,
              'first_updated': ops.first_updated,
              'last_updated': ops.last_updated,
              'histogram': ops.histogram}
    return success(result=result)

@app.route('/tags/<id>', methods=['DELETE'])
@login_required
def delete_tag(id):
    tag = current_user.tags.filter_by(id=id).first_or_404()
    tag.delete()
    return success()

@app.route('/activity', methods=['GET'])
@login_required
def activity():
    start = request.args.get('start', None)
    end = request.args.get('end', None)
    ops = DataOperations(current_user.repositories, start=start, end=end)
    result = {'first_updated': ops.first_updated,
              'last_updated': ops.last_updated,
              'histogram': ops.histogram}
    return success(result=result)

@app.route('/actions/refresh/<id>', methods=['GET'])
@login_required
def refresh_repository(id):
    repository = current_user.repositories.filter_by(id=id).first_or_404()
    repository.refresh()
    repository.update_commit_info()
    repository.save()
    return success()

@app.route('/actions/dump', methods=['GET'])
@login_required
def dump_repositories():
    si = io.StringIO()
    fake_csv = csv.writer(si)
    for repository in current_user.repositories.all():
        tags = ','.join([tag.name for tag in repository.tags])
        fake_csv.writerow([repository.name, repository.location, repository.kind, tags])
    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=repositories.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route('/actions/load', methods=['POST'])
@login_required
def load_repositories():
    if 'bulk-upload' not in request.files:
        return failure("'bulk-upload' parameter not found.")
    csv_file = request.files['bulk-upload']
    if not csv_file.filename:
        return failure('No file uploaded.')
    csv_path = save_uploaded_file(current_user, csv_file, app.config['UPLOAD_FOLDER'])
    with open(csv_path, 'r+') as f:
        for line in csv.reader(f):
            if not (isinstance(line, list) and len(line) == 4):
                return failure('Invalid format.')
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
