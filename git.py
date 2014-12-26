# pylint: disable=C0103,C0111,W0141

from itertools import islice, dropwhile, takewhile, groupby
from operator import itemgetter
from calendar import timegm
from datetime import date, timedelta

from pygit2 import Tag, Commit, Repository, Keypair, GitError, \
    clone_repository, \
    GIT_BRANCH_REMOTE, GIT_SORT_TOPOLOGICAL, \
    GIT_SORT_TIME, GIT_SORT_REVERSE
import re

class GitException(Exception):
    pass

class GitOperations(object):

    # where we store our git repos.
    git_repositories = 'repositories/'

    @staticmethod
    def git_uri_parse(git_repo):
        """Parse out git user/repository name from the git uri."""
        # strip the protocol if applicable
        stripped = git_repo
        if '://' in git_repo:
            _, _, stripped = git_repo.partition('://')
        # obtain the repository name.
        results = stripped.split('/')
        repository_name = results[-1]
        if not '.git' in repository_name:
            repository_name += '.git'
        # obtain the git user (default is 'git')
        git_username = 'git'
        if '@' in results[0]:
            git_username = results[0].split('@')[0]
        return git_username, repository_name

    @staticmethod
    def get_credentials(git_user, user):
        return Keypair(git_user,
                       user.ssh_public_key_path,
                       user.ssh_private_key_path,
                       '')

    @staticmethod
    def create_repository(user, git_repo):
        from models import Repository as LocalRepository
        try:
            git_user, git_name = GitOperations.git_uri_parse(git_repo)
            creds = GitOperations.get_credentials(git_user, user)
            where = GitOperations.git_repositories + git_name
            clone_repository(git_repo, where, bare=True, credentials=creds)
            repo = LocalRepository(user, git_user, git_name, git_repo).save()
            return repo
        except GitError as e:
            raise GitException(e.args)
        except ValueError as e:
            raise GitException(e.args)

class GitMixin(object):

    tag_regex = re.compile('^refs/tags')
    tag_or_remote_regex = re.compile('^refs/(tags|remotes)')

    def __init__(self):
        self.ondisk = Repository(GitOperations.git_repositories + self.name)

    def refresh(self):
        progress_bars = [remote.fetch() for remote in self.ondisk.remotes]
        for progress_bar in progress_bars:
            while progress_bar.received_objects != progress_bar.total_objects:
                print(progress_bar.received_objects + '/' +
                      progress_bar.total_objects)
        # update current reference
        master_ref = self.ondisk.lookup_reference('refs/heads/master')
        remote_ref = self.ondisk.lookup_reference('refs/remotes/origin/master')
        master_ref.set_target(remote_ref.target)

    def filter_references(self, regex):
        return [ref for ref in self.ondisk.listall_references()
                if regex.match(ref)]

    def get_tags(self):
        return self.filter_references(GitMixin.tag_regex)

    def get_branches(self):
        return self.ondisk.listall_branches(GIT_BRANCH_REMOTE)

    def get_commits(self, count=None):
        all_commits = self.ondisk.walk(self.ondisk.head.target,
                                       GIT_SORT_TOPOLOGICAL)
        if not count:
            return all_commits
        return islice(all_commits, count)

    def get_commit_count(self):
        return len(list(self.ondisk.walk(self.ondisk.head.target)))

    def get_latest_refs(self, count=None):
        info = self.filter_references(GitMixin.tag_or_remote_regex)
        refs = list(zip(info, map(self.get_commit_time, info)))
        refs.sort(key=itemgetter(1), reverse=True)
        if not count:
            return refs
        return islice(refs, count)

    def get_commit_time(self, name):
        ref = self.ondisk.revparse_single(name)
        if isinstance(ref, Tag):
            return ref.get_object().commit_time
        if isinstance(ref, Commit):
            return ref.commit_time
        raise GitException('invalid reference: commit time could not be found.')

    def get_shorthand_of_branch(self, branch):
        return self.ondisk.lookup_branch(branch).shorthand

    def get_sha1_of_branch(self, branch):
        return str(self.ondisk.lookup_branch(branch).get_object().id)[:6]

    def get_numstat(self, commit):
        previous_commit = self.ondisk.revparse_single(str(commit.id) + '^')
        diff = self.ondisk.diff(previous_commit, commit)
        additions, deletions = 0, 0
        for patch in diff:
            additions += patch.additions
            deletions += patch.deletions
        return (len(diff), additions, deletions)

    def get_first_updated(self):
        all_commits = self.ondisk.walk(self.ondisk.head.target,
                                       GIT_SORT_TIME | GIT_SORT_REVERSE)
        first_commit = next(all_commits)
        return first_commit.commit_time

    def get_last_updated(self):
        all_commits = self.ondisk.walk(self.ondisk.head.target,
                                       GIT_SORT_TIME)
        last_commit = next(all_commits)
        return last_commit.commit_time

    def get_file_count(self):
        diff = self.ondisk.head.get_object().tree.diff_to_tree()
        return len([patch.old_file_path for patch in diff])

    def get_line_count(self):
        diff = self.ondisk.head.get_object().tree.diff_to_tree()
        return sum([patch.deletions for patch in diff])

    def get_author_count(self):
        commits = self.ondisk.walk(self.ondisk.head.target)
        return len(set([commit.author.email for commit in commits]))

    def histogram(self, start, end):
        all_commits = self.ondisk.walk(self.ondisk.head.target,
                                       GIT_SORT_TIME | GIT_SORT_REVERSE)
        starting = dropwhile(lambda obj: obj.commit_time < start, all_commits)
        series = takewhile(lambda obj: obj.commit_time <= end, starting)
        def keyfunc(obj):
            # we want to group our commit times by the day. so convert
            # timestamp -> date -> timestamp
            new_date = date.fromtimestamp(obj.commit_time)
            new_date += timedelta(days=1)
            return timegm(new_date.timetuple())
        result = groupby(series, keyfunc)
        return [{'date': commit_date,
                 'value': len(list(commits))}
                for commit_date, commits in result]

if __name__ == "__main__":
    repos = [
        ('git://github.com/rails/rails.git', 'git', 'rails.git'),
        ('git@github.com:cantsin/random-repo', 'git', 'random-repo.git'),
        ('https://github.com/cantsin/test.git', 'git', 'test.git'),
        ('ssh://git@github.com/cantsin/test-2.git', 'git', 'test-2.git'),
        ('git@github.com:cantsin/test-3.git', 'git', 'test-3.git'),
        ('git@bitbucket.org:accountname/reponame.git', 'git', 'reponame.git'),
        ('ssh://git@bitbucket.org/account/reponame.git', 'git', 'reponame.git'),
        ('https://foo@bitbucket.org/foo/reponame.git', 'foo', 'reponame.git'),
        ('james@foo:random/testing.git', 'james', 'testing.git')]
    for test_repo, test_user, test_name in repos:
        assert GitOperations.git_uri_parse(test_repo) == (test_user, test_name)
