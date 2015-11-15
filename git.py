# pylint: disable=C0103,C0111,W0141

from itertools import islice, dropwhile, takewhile, groupby
from operator import itemgetter
from calendar import timegm
from datetime import date, timedelta

from pygit2 import Tag, Commit, Repository, Keypair, GitError, \
    GIT_SORT_TOPOLOGICAL, GIT_SORT_TIME, GIT_SORT_REVERSE, \
    clone_repository
import re
import os

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
        if ':' in repository_name:
            # did not work. try again.
            results = stripped.split(':')
            repository_name = results[-1]
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
    def get_repository_location(user, git_name):
        return os.path.join(GitOperations.git_repositories,
                            str(user.id),
                            git_name)

    @staticmethod
    def create_repository(user, git_repo):
        from models import Repository as LocalRepository
        try:
            git_user, git_name = GitOperations.git_uri_parse(git_repo)
            creds = GitOperations.get_credentials(git_user, user)
            where = GitOperations.get_repository_location(user, git_name)
            clone_repository(git_repo, where, bare=True, credentials=creds)
            repo = LocalRepository(user, git_user, git_name, git_repo).save()
            return repo
        except GitError as e:
            raise GitException(e.args)
        except ValueError as e: # pragma: no cover
            raise GitException(e.args)

class GitMixin(object):

    tag_or_remote_regex = re.compile('^refs/(tags|remotes)/(.*)')

    def __init__(self):
        where = GitOperations.get_repository_location(self.user, self.name)
        self.ondisk = Repository(where)

    def refresh(self):
        creds = GitOperations.get_credentials(self.git_user, self.user)
        for remote in self.ondisk.remotes:
            remote.credentials = creds
            remote.fetch()
        # update current reference
        master_ref = self.ondisk.lookup_reference('refs/heads/master')
        remote_ref = self.ondisk.lookup_reference('refs/remotes/origin/master')
        master_ref.set_target(remote_ref.target)

    def filter_references(self, regex):
        return [ref for ref in self.ondisk.listall_references()
                if regex.match(ref)]

    def get_commit_time(self, name):
        ref = self.ondisk.revparse_single(name)
        if isinstance(ref, Tag):
            return ref.get_object().commit_time
        if isinstance(ref, Commit):
            return ref.commit_time
        raise GitException('invalid reference: commit time could not be found.') # pragma: no cover

    def get_latest_refs(self, count=None):
        info = self.filter_references(GitMixin.tag_or_remote_regex)
        refs = list(zip(info, map(self.get_commit_time, info)))
        refs.sort(key=itemgetter(1), reverse=True)
        def ref_info(info):
            (ref, commit_time) = info
            what, name = GitMixin.tag_or_remote_regex.findall(ref)[0]
            return (what, name, commit_time)
        refs = map(ref_info, refs)
        if not count:
            return refs
        return islice(refs, count)

    def filter_commits(self, flags=0):
        all_commits = self.ondisk.walk(self.ondisk.head.target, flags)
        emails = [ue.email for ue in self.user.emails.all()]
        return filter(lambda commit: commit.author.email in emails, all_commits)

    def get_commits(self, count=None):
        all_commits = self.filter_commits(GIT_SORT_TOPOLOGICAL)
        if not count:
            return all_commits
        return islice(all_commits, count)

    def get_commit_count(self):
        return len(list(self.filter_commits()))

    def get_shorthand_of_branch(self, branch):
        commit = self.ondisk.lookup_branch(branch)
        if commit:
            return commit.shorthand
        return '(none)'

    def get_sha1_of_branch(self, branch):
        commit = self.ondisk.lookup_branch(branch)
        if commit:
            return str(commit.get_object().id)[:6]
        return '(none)'

    def get_numstat(self, commit):
        diff = None
        try:
            previous_commit = self.ondisk.revparse_single(str(commit.id) + '^')
            diff = self.ondisk.diff(previous_commit, commit)
        except KeyError:
            # likely we hit the very first commit.
            diff = commit.tree.diff_to_tree(swap=True)
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
        commits = self.filter_commits()
        return len(set([commit.author.email for commit in commits]))

    def commits_between(self, start, end):
        all_commits = self.filter_commits(GIT_SORT_TIME | GIT_SORT_REVERSE)
        starting = dropwhile(lambda obj: obj.commit_time < start, all_commits)
        return takewhile(lambda obj: obj.commit_time <= end, starting)

    @staticmethod
    def by_day(obj):
        # we want to group our commit times by the day. so convert
        # timestamp -> date -> timestamp
        new_date = date.fromtimestamp(obj.commit_time)
        new_date += timedelta(days=1)
        return timegm(new_date.timetuple())

    @staticmethod
    def group_by(series):
        result = groupby(series, GitMixin.by_day)
        return [{'date': commit_date,
                 'value': len(list(commits))}
                for commit_date, commits in result]

    def histogram(self, start, end):
        series = self.commits_between(start, end)
        return GitMixin.group_by(series)
