# pylint: disable=C0103,C0111

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy, orm
from flask.ext.login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from .util import slugify
from .git import GitMixin
from tracker import app

db = SQLAlchemy(app)

def init_db():
    # create the tables if it doesn't already exist.
    db.create_all()
    db.session.commit()

class SessionMixin(object):
    def save(self):
        self.updated_at = datetime.now()
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class User(SessionMixin, UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(255), nullable=False, unique=True)
    password = orm.deferred(db.Column(db.String(255), nullable=False))
    ssh_public_key_path = db.Column(db.Text())
    ssh_private_key_path = db.Column(db.Text())
    avatar_image = db.Column(db.String(255))
    active = db.Column(db.Boolean(), nullable=False, default=True)
    created_at = db.Column(db.DateTime(), nullable=False)
    updated_at = db.Column(db.DateTime(), nullable=False)

    def __init__(self, login, password):
        self.login = login
        self.password = generate_password_hash(password)
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def __repr__(self):
        return '<User %r>' % self.id

    def add_emails(self, emails):
        if not isinstance(emails, list):
            emails = [emails]
        for email in emails:
            user_email = UserEmail(self, email).save()
            self.emails.append(user_email)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_active(self):
        return self.active

    def public_key_name(self):
        return self.ssh_public_key_path.split('/')[-1]

    def private_key_name(self):
        return self.ssh_private_key_path.split('/')[-1]

class UserEmail(SessionMixin, db.Model): #pylint: disable-msg=R0903
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('emails',
                                                      cascade='all,delete',
                                                      lazy='dynamic'))
    created_at = db.Column(db.DateTime(), nullable=False)
    updated_at = db.Column(db.DateTime(), nullable=False)

    def __init__(self, user, email):
        self.user_id = user.id
        self.email = email
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def __repr__(self):
        return '<Email %r for %r>' % (self.email, self.user)

tags = db.Table('tags',
                db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                db.Column('repository_id', db.Integer, db.ForeignKey('repository.id')))

class Repository(SessionMixin, GitMixin, db.Model): #pylint: disable-msg=R0904
    LOCAL = 'local'
    GITHUB = 'github'
    BITBUCKET = 'bitbucket'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User',
                           backref=db.backref('repositories',
                                              cascade='all,delete',
                                              lazy='dynamic'))
    tags = db.relationship('Tag',
                           secondary=tags,
                           backref=db.backref('repositories',
                                              cascade='all,delete',
                                              lazy='dynamic'))
    git_user = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    kind = db.Column(db.String(255), nullable=False) # GITHUB, BITBUCKET, LOCAL
    location = db.Column(db.String(255), nullable=False)
    first_commit = db.Column(db.DateTime())
    last_commit = db.Column(db.DateTime())
    created_at = db.Column(db.DateTime(), nullable=False)
    updated_at = db.Column(db.DateTime(), nullable=False)

    def __init__(self, user, git_user, name, location):
        self.user_id = user.id
        self.git_user = git_user
        self.name = name
        self.location = location
        self.kind = Repository.LOCAL
        if 'github' in location:
            self.kind = Repository.GITHUB
        if 'bitbucket' in location:
            self.kind = Repository.BITBUCKET
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def update_commit_info(self):
        self.reconstruct()
        self.first_commit = datetime.fromtimestamp(self.get_first_updated())
        self.last_commit = datetime.fromtimestamp(self.get_last_updated())
        self.save()

    # initialize GitMixin
    @orm.reconstructor
    def reconstruct(self):
        GitMixin.__init__(self)

    def clear_tags(self):
        query = tags.delete().where(tags.c.repository_id == self.id)
        db.session.execute(query)
        db.session.commit()

    def __repr__(self):
        return '<Repository %r (%r)>' % (self.name, self.kind)

class Tag(SessionMixin, db.Model): #pylint: disable-msg=R0903
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User',
                           backref=db.backref('tags',
                                              cascade='all,delete',
                                              lazy='dynamic'))
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)
    updated_at = db.Column(db.DateTime(), nullable=False)

    def __init__(self, user, name):
        self.user_id = user.id
        self.name = name
        self.slug = slugify(name)
        self.count = 0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def __repr__(self):
        return '<Tag %r>' % self.name
