from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy, orm
from flask.ext.login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from util import slugify
from git import GitMixin

app = Flask("git-tracker")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

class SaveMixin(object):
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

class User(SaveMixin, UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = orm.deferred(db.Column(db.String(255), nullable=False))
    ssh_public_key_path = db.Column(db.Text())
    ssh_private_key_path = db.Column(db.Text())
    avatar_image = db.Column(db.String(255))
    is_active = db.Column(db.Boolean(), nullable=False, default=True)
    created_at = db.Column(db.DateTime(), nullable=False)
    updated_at = db.Column(db.DateTime(), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __init__(self, email, password, ssh_key):
        self.email = email
        self.password = generate_password_hash(password)
        self.ssh_key = ssh_key
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def __repr__(self):
        return '<User %r>' % self.email

    def is_active(self):
        return self.is_active

tags = db.Table('tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('repository_id', db.Integer, db.ForeignKey('repository.id'))
)

class Repository(SaveMixin, GitMixin, db.Model):
    LOCAL = "local"
    GITHUB = "github"
    BITBUCKET = "bitbucket"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User',
                           backref=db.backref('repositories', lazy='dynamic'))
    tags = db.relationship('Tag',
                           secondary=tags,
                           backref=db.backref('repositories', lazy='dynamic'))
    name = db.Column(db.String(255), nullable=False)
    kind = db.Column(db.String(255), nullable=False) # GITHUB, BITBUCKET, or LOCAL
    location = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)
    updated_at = db.Column(db.DateTime(), nullable=False)

    def __init__(self, user, name, location, kind):
        self.user_id = user.id
        self.name = name
        self.location = location
        self.kind = kind
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    # initialize GitMixin
    @orm.reconstructor
    def reconstruct(self):
        self.connect_to_disk()

    def get_name(self):
        return self.name[:-4] # strip .git suffix

    def __repr__(self):
        return '<Repository %r (%r)>' % (self.name, self.kind)

class Tag(SaveMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User',
                           backref=db.backref('tags', lazy='dynamic'))
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
