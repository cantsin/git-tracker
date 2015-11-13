from app import app

from flask import Request
from flask.json import loads
from werkzeug import FileStorage
from werkzeug.datastructures import MultiDict

from models import init_db, Repository
from git import GitOperations

import os
import unittest
import tempfile
import shutil
from json import dumps
from io import StringIO

class TestingFileStorage(FileStorage):
    def __init__(self, stream=None, filename=None, name=None,
                 content_type='application/octet-stream', content_length=-1,
                 headers=None):
        FileStorage.__init__(
            self, stream, filename, name=name,
            content_type=content_type, content_length=content_length,
            headers=None)
        self.saved = None

    def save(self, dst, buffer_size=16384):
        if isinstance(dst, basestring):
            self.saved = dst
        else:
            self.saved = dst.name

class GitTrackerTestCase(unittest.TestCase):

    # where we store our git repos.
    git_repositories = 'test/repositories/'

    def setUp(self):
        GitOperations.git_repositories = GitTrackerTestCase.git_repositories
        with app.app_context():
            self.db_fd, location = tempfile.mkstemp()
            init_db(location)
            app.config['DATABASE'] = location
            app.config['TESTING'] = True
            app.config['CSRF_ENABLED'] = False
            app.secret_key = os.urandom(24)
            self.app = app.test_client()
        try:
            os.makedirs(GitTrackerTestCase.git_repositories)
        except FileExistsError:
            pass
        self.initialize()

    # helper functions.
    def initialize(self): pass

    def get(self, where, **kwargs):
        data = dumps(kwargs)
        result = self.app.get(where, data=data, content_type='application/json')
        return loads(result.get_data())

    def post(self, where, **kwargs):
        data = dumps(kwargs)
        result = self.app.post(where, data=data, content_type='application/json')
        return loads(result.get_data())

    def delete(self, where, **kwargs):
        data = dumps(kwargs)
        result = self.app.delete(where, data=data, content_type='application/json')
        return loads(result.data)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
        shutil.rmtree(GitTrackerTestCase.git_repositories)

class UserTestCase(GitTrackerTestCase):

    def test_404(self):
        result = self.post('/invalid')
        assert result['success'] == False
        assert '404: Not Found' in result['error']

    def test_add_empty_user(self):
        result = self.post('/users')
        assert result['success'] == False
        assert 'email not found' in result['errors']

    def test_add_user_no_at(self):
        result = self.post('/users', email='someone')
        assert result['success'] == False
        assert 'Please provide a proper email.' in result['errors']

    def test_add_user_mismatched_passwords(self):
        user_data = dict(email='someone@some.org', password='test', password2='')
        result = self.post('/users', **user_data)
        assert result['success'] == False
        assert 'Passwords do not match.' in result['errors']

    def test_add_user_success(self):
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/users', **user_data)
        assert result['success'] == True

    def test_invalid_login(self):
        user_data = dict(email='someone2@some.org', password='test', password2='test')
        result = self.post('/users', **user_data)
        assert result['success'] == True
        user_data['password'] = ''
        result = self.post('/login', **user_data)
        assert 'Email and password do not match.' in result['errors']

    def test_successful_login(self):
        user_data = dict(email='someone3@some.org', password='test', password2='test')
        result = self.post('/users', **user_data)
        assert result['success'] == True
        result = self.post('/login', **user_data)
        assert result['success'] == True

    def test_successful_logout(self):
        user_data = dict(email='someone4@some.org', password='test', password2='test')
        result = self.post('/users', **user_data)
        assert result['success'] == True
        result = self.post('/login', **user_data)
        assert result['success'] == True
        result = self.app.get('/logout')
        result = loads(result.data)
        assert result['success'] == True

class EmailTestCase(GitTrackerTestCase):

    def initialize(self):
        # create random user and login
        user_data = dict(email='someone5@some.org', password='test', password2='test')
        result = self.post('/login', **user_data)
        if result['success'] != True:
            result = self.post('/users', **user_data)
            assert result['success'] == True
            result = self.post('/login', **user_data)
            assert result['success'] == True

    def test_add_email(self):
        email_data = dict(email='newemail@foo.org')
        result = self.post('/emails', **email_data)
        assert result['success'] == True

    def test_add_email_no_at(self):
        email_data = dict(email='newemailfoo.org')
        result = self.post('/emails', **email_data)
        assert 'Please provide a proper email.' in result['errors']

    def test_add_email_duplicate(self):
        email_data = dict(email='someone5@some.org')
        result = self.post('/emails', **email_data)
        assert 'Current email already exists.' in result['errors']

    def test_delete_email(self):
        result = self.delete('/emails/1')
        assert result['success'] == True

    def test_delete_email_invalid(self):
        result = self.delete('/emails/9999')
        assert '404' in result['error']

class RepositoryTestCase(GitTrackerTestCase):

    def initialize(self):
        # create random user and login
        user_data = dict(email='someone6@some.org', password='test', password2='test')
        result = self.post('/login', **user_data)
        if result['success'] != True:
            result = self.post('/users', **user_data)
            assert result['success'] == True
            result = self.post('/login', **user_data)
            assert result['success'] == True
        Repository.query.delete()
        # create repository
        result = self.get('/repositories/1')
        if result['success'] != True:
            repo_data = dict(location='git://git@github.com/cantsin/git-tracker')
            result = self.post('/repositories', **repo_data)
            assert result['success'] == True

    def test_add_repository(self):
        repo_data = dict(location='git://git@github.com/cantsin/dotemacs')
        result = self.post('/repositories', **repo_data)
        assert result['success'] == True

    def test_add_repository_invalid(self):
        repo_data = dict(location='git://git@github.com/cantsin/_invalid')
        result = self.post('/repositories', **repo_data)
        assert 'Repository not found.' in result['errors'][0]

    def test_add_repository_duplicate(self):
        repo_data = dict(location='git://git@github.com/cantsin/git-tracker')
        result = self.post('/repositories', **repo_data)
        assert 'Given repository already exists.' in result['errors']

    def test_view_repository(self):
        result = self.get('/repositories/1')
        assert result['success']

    def test_view_repository_invalid(self):
        result = self.get('/repositories/9999')
        assert '404' in result['error']

    def test_delete_repository(self):
        result = self.delete('/repositories/1')
        assert result['success']

    def test_delete_repository_invalid(self):
        result = self.delete('/repositories/9999')
        assert '404' in result['error']

    def test_repository_activity(self):
        result = self.get('/repositories/1/activity')
        assert result['success']

    def test_repository_activity_invalid(self):
        result = self.get('/repositories/9999/activity')
        assert '404' in result['error']

if __name__ == '__main__':
    unittest.main()
