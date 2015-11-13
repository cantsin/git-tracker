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

class UserTestCase(unittest.TestCase):

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

class EmailTestCase(unittest.TestCase):

    def setUp(self):
        with app.app_context():
            self.db_fd, location = tempfile.mkstemp()
            init_db(location)
            app.config['DATABASE'] = location
            app.config['TESTING'] = True
            app.config['CSRF_ENABLED'] = False
            app.secret_key = os.urandom(24)
            self.app = app.test_client()
        # create random user and login
        user_data = dict(email='someone5@some.org', password='test', password2='test')
        result = self.post('/login', **user_data)
        if result['success'] != True:
            result = self.post('/users', **user_data)
            assert result['success'] == True
            result = self.post('/login', **user_data)
            assert result['success'] == True

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def post(self, where, **kwargs):
        data = dumps(kwargs)
        result = self.app.post(where, data=data, content_type='application/json')
        return loads(result.data)

    def delete(self, where, **kwargs):
        data = dumps(kwargs)
        result = self.app.delete(where, data=data, content_type='application/json')
        return loads(result.data)

    def test_add_email(self):
        email_data = dict(email='newemail@foo.org')
        result = self.post('/emails/', **email_data)
        assert result['success'] == True

    def test_add_email_no_at(self):
        email_data = dict(email='newemailfoo.org')
        result = self.post('/emails/', **email_data)
        assert 'Please provide a proper email.' in result['errors']

    def test_add_email_duplicate(self):
        email_data = dict(email='someone5@some.org')
        result = self.post('/emails/', **email_data)
        assert 'Current email already exists.' in result['errors']

    def test_delete_email(self):
        result = self.delete('/emails/1')
        assert result['success'] == True

    def test_delete_email_invalid(self):
        result = self.delete('/emails/9999')
        assert '404' in result['error']

if __name__ == '__main__':
    unittest.main()
