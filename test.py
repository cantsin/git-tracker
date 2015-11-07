from app import app

from flask import Request
from flask.json import loads
from werkzeug import FileStorage
from werkzeug.datastructures import MultiDict

from models import init_db

import os
import unittest
import tempfile
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

    def setUp(self):
        with app.app_context():
            self.db_fd, location = tempfile.mkstemp()
            init_db(location)
            app.config['DATABASE'] = location
            app.config['TESTING'] = True
            app.config['CSRF_ENABLED'] = False
            app.secret_key = os.urandom(24)
            self.app = app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def post(self, where, **kwargs):
        data = dumps(kwargs)
        result = self.app.post(where, data=data, content_type='application/json')
        return loads(result.data)

    def test_add_empty_user(self):
        result = self.post('/users/add')
        assert result['success'] == False
        assert 'email not found' in result['error']

    def test_add_user_no_ampersand(self):
        result = self.post('/users/add', email='someone')
        assert result['success'] == False
        assert 'Please provide a proper email' in result['error']

    def test_add_user_mismatched_passwords(self):
        user_data = dict(email='someone@some.org', password='test', password2='')
        result = self.post('/users/add', **user_data)
        assert result['success'] == False
        assert 'Passwords do not match' in result['error']

    def test_add_user_success(self):
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/users/add', **user_data)
        assert result['success'] == True

    def test_invalid_login(self):
        user_data = dict(email='someone2@some.org', password='test', password2='test')
        result = self.post('/users/add', **user_data)
        assert result['success'] == True
        user_data['password'] = ''
        result = self.post('/login', **user_data)
        assert 'Email and password do not match' in result['error']

    def test_successful_login(self):
        user_data = dict(email='someone3@some.org', password='test', password2='test')
        result = self.post('/users/add', **user_data)
        assert result['success'] == True
        result = self.post('/login', **user_data)
        assert result['success'] == True

    def test_successful_logout(self):
        user_data = dict(email='someone4@some.org', password='test', password2='test')
        result = self.post('/users/add', **user_data)
        assert result['success'] == True
        result = self.post('/login', **user_data)
        assert result['success'] == True
        result = self.app.get('/logout')
        result = loads(result.data)
        assert result['success'] == True

if __name__ == '__main__':
    unittest.main()
