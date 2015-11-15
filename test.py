from app import app

from flask import Request
from flask.json import loads
from werkzeug import FileStorage
from werkzeug.datastructures import MultiDict

from models import init_db, User, Repository, Tag, UserEmail
from git import GitOperations

import io
import os
import unittest
import tempfile
import shutil
from json import dumps
from io import StringIO

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
            app.config['UPLOAD_FOLDER'] = 'test/uploads/'
            app.secret_key = os.urandom(24)
            self.app = app.test_client()
        try:
            shutil.rmtree(GitTrackerTestCase.git_repositories)
        except FileNotFoundError:
            pass
        try:
            os.makedirs(GitTrackerTestCase.git_repositories)
        except FileExistsError: # pragma: no cover
            pass
        # clear database.
        Repository.query.delete()
        User.query.delete()
        UserEmail.query.delete()
        Tag.query.delete()
        self.initialize()

    # helper functions.
    def initialize(self): pass

    def get(self, where, **kwargs):
        query = kwargs.pop('query', {})
        data = dumps(kwargs)
        result = self.app.get(where, data=data, query_string=query, content_type='application/json')
        return loads(result.get_data())

    def put(self, where, **kwargs):
        data = dumps(kwargs)
        result = self.app.put(where, data=data, content_type='application/json')
        return loads(result.get_data())

    def put_files(self, where, files):
        result = self.app.put(where, data=files)
        return loads(result.get_data())

    def post(self, where, **kwargs):
        data = dumps(kwargs)
        result = self.app.post(where, data=data, content_type='application/json')
        return loads(result.get_data())

    def post_files(self, where, files):
        result = self.app.post(where, data=files)
        return loads(result.get_data())

    def delete(self, where, **kwargs):
        data = dumps(kwargs)
        result = self.app.delete(where, data=data, content_type='application/json')
        return loads(result.data)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
        shutil.rmtree(GitTrackerTestCase.git_repositories)

class GitTestCase(GitTrackerTestCase):

    repos = [
        ('git://github.com/rails/rails.git', 'git', 'rails.git'),
        ('git@github.com:cantsin/random-repo', 'git', 'random-repo.git'),
        ('https://github.com/cantsin/test.git', 'git', 'test.git'),
        ('ssh://git@github.com/cantsin/test-2.git', 'git', 'test-2.git'),
        ('git@github.com:cantsin/test-3.git', 'git', 'test-3.git'),
        ('git@bitbucket.org:accountname/reponame.git', 'git', 'reponame.git'),
        ('ssh://git@bitbucket.org/account/reponame.git', 'git', 'reponame.git'),
        ('https://foo@bitbucket.org/foo/reponame.git', 'foo', 'reponame.git'),
        ('james@foo:random/testing.git', 'james', 'testing.git'),
        ('git@random-server:random.git', 'git', 'random.git')]

    def test_uri_parse(self):
        for test_repo, test_user, test_name in GitTestCase.repos:
            assert GitOperations.git_uri_parse(test_repo) == (test_user, test_name)

class UserTestCase(GitTrackerTestCase):

    def test_404(self):
        result = self.post('/invalid')
        assert result['success'] == False
        assert '404: Not Found' in result['error']

    def test_user_repr(self):
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/users', **user_data)
        assert result['success']
        e = UserEmail.query.first()
        assert 'someone@some.org' in repr(e)

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
        assert result['success']

    def test_invalid_login(self):
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/users', **user_data)
        assert result['success']
        user_data['password'] = ''
        result = self.post('/login', **user_data)
        assert 'Email and password do not match.' in result['errors']

    def test_successful_login(self):
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/users', **user_data)
        assert result['success']
        result = self.post('/login', **user_data)
        assert result['success']

    def test_successful_logout(self):
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/users', **user_data)
        assert result['success']
        result = self.post('/login', **user_data)
        assert result['success']
        result = self.get('/logout')
        assert result['success']

    def test_upload_keys(self):
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/users', **user_data)
        assert result['success']
        result = self.post('/login', **user_data)
        assert result['success']
        files = {'public-key': (io.BytesIO(b'public'), 'key.pub'),
                 'private-key': (io.BytesIO(b'private'), 'key'), }
        result = self.put_files('/users', files)
        assert result['success']
        user = User.query.first()
        assert user.public_key_name() == 'key.pub'
        assert user.private_key_name() == 'key'

    def test_upload_keys_invalid(self):
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/users', **user_data)
        assert result['success']
        result = self.post('/login', **user_data)
        assert result['success']
        result = self.put('/users')
        assert 'Please fill out all fields.' in result['errors']

class EmailTestCase(GitTrackerTestCase):

    def initialize(self):
        # create random user and login
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/login', **user_data)
        if result['success'] != True:
            result = self.post('/users', **user_data)
            assert result['success']
            result = self.post('/login', **user_data)
            assert result['success']

    def test_get_emails(self):
        result = self.get('/emails')
        assert result['success']
        assert len(result['data']) == 1

    def test_email_repr(self):
        u = User.query.first()
        e = u.emails.first()
        assert 'someone' in repr(e)

    def test_add_email(self):
        email_data = dict(email='newemail@foo.org')
        result = self.post('/emails', **email_data)
        assert result['success']

    def test_add_email_no_at(self):
        email_data = dict(email='newemailfoo.org')
        result = self.post('/emails', **email_data)
        assert 'Please provide a proper email.' in result['errors']

    def test_add_email_duplicate(self):
        email_data = dict(email='someone@some.org')
        result = self.post('/emails', **email_data)
        assert 'Current email already exists.' in result['errors']

    def test_delete_email(self):
        result = self.delete('/emails/1')
        assert result['success']

    def test_delete_email_invalid(self):
        result = self.delete('/emails/9999')
        assert '404' in result['error']

class RepositoryTestCase(GitTrackerTestCase):

    def initialize(self):
        # create random user and login
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/login', **user_data)
        if result['success'] != True:
            result = self.post('/users', **user_data)
            assert result['success']
            result = self.post('/login', **user_data)
            assert result['success']
            email_data = dict(email='jtranovich@gmail.com')
            result = self.post('/emails', **email_data)
            assert result['success']
        # create repository (email must be a valid author of this repository)
        result = self.get('/repositories/1')
        if result['success'] != True:
            repo_data = dict(location='git://git@github.com/cantsin/git-tracker.git')
            result = self.post('/repositories', **repo_data)
            assert result['success']

    def test_get_repositories(self):
        result = self.get('/repositories')
        assert result['success']
        assert len(result['data']) == 1

    def test_repository_repr(self):
        r = Repository.query.first()
        assert 'git-tracker' in repr(r)

    def test_add_repository(self):
        repo_data = dict(location='https://bitbucket.org/cantsin/empty-repo')
        result = self.post('/repositories', **repo_data)
        assert result['success']

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
        assert result['data'] != []

    def test_view_repository_invalid(self):
        result = self.get('/repositories/9999')
        assert '404' in result['error']

    def test_view_repository_params(self):
        query = {'start': 0, 'end': 9999, 'reference_count': 7, 'commit_count': 10}
        result = self.get('/repositories/1', query=query)
        assert result['success']
        assert result['data']['histogram'] == []

    def test_delete_repository(self):
        result = self.delete('/repositories/1')
        assert result['success']

    def test_delete_repository_invalid(self):
        result = self.delete('/repositories/9999')
        assert '404' in result['error']

    def test_repository_add_tags(self):
        # create two tags.
        tag_data = dict(name='tag #1')
        result = self.post('/tags', **tag_data)
        assert result['success']
        tag_data = dict(name='tag #2')
        result = self.post('/tags', **tag_data)
        assert result['success']
        tag_ids = [tag.id for tag in Tag.query.all()]
        result = self.put('/repositories/1', **dict(ids=tag_ids))
        assert result['success']

    def test_repository_add_tags_mixed_invalid(self):
        # create two tags.
        tag_data = dict(name='tag #1')
        result = self.post('/tags', **tag_data)
        assert result['success']
        tag_data = dict(name='tag #2')
        result = self.post('/tags', **tag_data)
        assert result['success']
        tag_ids = [tag.id for tag in Tag.query.all()]
        tag_ids.extend([9999])
        result = self.put('/repositories/1', **dict(ids=tag_ids))
        assert '404' in result['error']

    def test_repository_add_tags_invalid(self):
        result = self.put('/repositories/9999')
        assert '404' in result['error']

class TagTestCase(GitTrackerTestCase):

    def initialize(self):
        # create random user and login
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/login', **user_data)
        if result['success'] != True:
            result = self.post('/users', **user_data)
            assert result['success']
            result = self.post('/login', **user_data)
            assert result['success']
        # create tag
        tag_data = dict(name='Some tag')
        result = self.post('/tags', **tag_data)
        assert result['success']

    def test_get_tags(self):
        result = self.get('/tags')
        assert result['success']
        assert len(result['data']) == 1

    def test_tag_repr(self):
        t = Tag.query.first()
        assert 'Some tag' in repr(t)

    def test_add_tag(self):
        tag_data = dict(name='Some new tag')
        result = self.post('/tags', **tag_data)
        assert result['success']

    def test_add_blank_tag(self):
        tag_data = dict(name='')
        result = self.post('/tags', **tag_data)
        assert 'Tag cannot be blank.' in result['errors']

    def test_add_duplicate_tag(self):
        tag_data = dict(name='Some tag')
        result = self.post('/tags', **tag_data)
        assert 'Given tag name already exists.' in result['errors']

    def test_add_duplicate_slug(self):
        tag_data = dict(name='some tag')
        result = self.post('/tags', **tag_data)
        assert 'Given tag slug already exists.' in result['errors']

    def test_delete_tag(self):
        result = self.delete('/tags/1')
        assert result['success']

    def test_delete_tag_invalid(self):
        result = self.delete('/tags/9999')
        assert '404' in result['error']

    def test_view_tag(self):
        # create a repository.
        repo_data = dict(location='git://git@github.com/cantsin/git-tracker')
        result = self.post('/repositories', **repo_data)
        assert result['success']
        # add associated email.
        email_data = dict(email='jtranovich@gmail.com')
        result = self.post('/emails', **email_data)
        assert result['success']
        # add this tag.
        tag = Tag.query.first()
        repo = Repository.query.first()
        repo.tags.append(tag)
        repo.save()
        # test activity results.
        result = self.get('/tags/1')
        assert result['success']
        assert result['data'] != []

    def test_view_tag_params(self):
        result = self.get('/tags/1', query={'start': 0, 'end': 9999})
        assert result['success']
        assert result['data']['histogram'] == []

    def test_view_tag_invalid(self):
        result = self.get('/tags/9999')
        assert '404' in result['error']

class ActivityTestCase(GitTrackerTestCase):

    def initialize(self):
        # create random user and login
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/login', **user_data)
        if result['success'] != True:
            result = self.post('/users', **user_data)
            assert result['success']
            result = self.post('/login', **user_data)
            assert result['success']
            email_data = dict(email='jtranovich@gmail.com')
            result = self.post('/emails', **email_data)
            assert result['success']
        # create repository (email must be a valid author of this repository)
        result = self.get('/repositories/1')
        if result['success'] != True:
            repo_data = dict(location='git://git@github.com/cantsin/git-tracker')
            result = self.post('/repositories', **repo_data)
            assert result['success']

    def test_activity(self):
        result = self.get('/activity')
        assert result['success']

    def test_activity_params(self):
        result = self.get('/activity', query={'start': 0, 'end': 9999})
        assert result['success']
        assert result['data']['histogram'] == []

class ActionTestCase(GitTrackerTestCase):

    def initialize(self):
        # create random user and login
        user_data = dict(email='someone@some.org', password='test', password2='test')
        result = self.post('/login', **user_data)
        if result['success'] != True:
            result = self.post('/users', **user_data)
            assert result['success']
            result = self.post('/login', **user_data)
            assert result['success']
            email_data = dict(email='jtranovich@gmail.com')
            result = self.post('/emails', **email_data)
            assert result['success']
        # create repository (email must be a valid author of this repository)
        result = self.get('/repositories/1')
        if result['success'] != True:
            repo_data = dict(location='git://git@github.com/cantsin/git-tracker')
            result = self.post('/repositories', **repo_data)
            assert result['success']

    def test_action_refresh(self):
        result = self.get('/actions/refresh/1')
        assert result['success']

    def test_action_refresh_invalid(self):
        result = self.get('/actions/refresh/9999')
        assert '404' in result['error']

    def test_action_dump(self):
        result = self.app.get('/actions/dump')
        assert result.headers[0] == ('Content-Type', 'text/csv')
        assert b'git-tracker' in result.get_data()

    def test_action_load(self):
        csv_data = b'git-tracker,git://git@github.com/cantsin/git-tracker,github,'
        files = {'bulk-upload': (io.BytesIO(csv_data), 'test.csv') }
        result = self.post_files('/actions/load', files)
        assert result['success']

    def test_action_load_with_tags(self):
        u = User.query.first()
        Tag(u, 'metrics').save()
        Tag(u, 'analytics').save()
        csv_data = b'git-tracker,git://git@github.com/cantsin/git-tracker,github,"metrics,analytics"'
        files = {'bulk-upload': (io.BytesIO(csv_data), 'test.csv') }
        result = self.post_files('/actions/load', files)
        assert result['success']

    def test_action_load_repos_with_tags(self):
        u = User.query.first()
        Tag(u, 'metrics').save()
        Tag(u, 'analytics').save()
        csv_data = b'git-tracker,git://git@github.com/cantsin/git-tracker,github,"metrics,analytics"\n' + \
                   b'empty,https://bitbucket.org/cantsin/empty-repo,bitbucket,'
        files = {'bulk-upload': (io.BytesIO(csv_data), 'test.csv') }
        result = self.post_files('/actions/load', files)
        assert result['success']

    def test_action_load_wrong_csv(self):
        files = {'bulk-upload': (io.BytesIO(b'what,the,hey'), 'test.csv') }
        result = self.post_files('/actions/load', files)
        assert 'Invalid format.' in result['errors']

    def test_action_load_invalid(self):
        files = {'bulk-upload': (io.BytesIO(b'invalid'), '')}
        result = self.post_files('/actions/load', files)
        assert "No file uploaded." in result['errors']

    def test_action_load_invalid2(self):
        files = {'test': (io.BytesIO(b'invalid'), 'invalid')}
        result = self.post_files('/actions/load', files)
        assert "'bulk-upload' parameter not found." in result['errors']

if __name__ == '__main__':
    unittest.main()
