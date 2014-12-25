# pylint: disable=C0103,C0111

from operator import itemgetter
from itertools import islice

from pygit2 import Tag, Commit, Repository, \
    GIT_BRANCH_REMOTE, GIT_SORT_TOPOLOGICAL, GIT_SORT_TIME
import re

class GitException(Exception):
    pass

class GitMixin(object):

    tag_regex = re.compile('^refs/tags')
    tag_or_remote_regex = re.compile('^refs/(tags|remotes)')

    def connect_to_disk(self):
        self.ondisk = Repository('repositories/' + self.name)

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
        all_commits = self.ondisk.walk(self.ondisk.head.target, GIT_SORT_TIME)
        first_commit = next(all_commits)
        return first_commit.commit_time

    def get_last_updated(self):
        return self.ondisk.head.get_object().commit_time

    def get_file_count(self):
        diff = self.ondisk.head.get_object().tree.diff_to_tree()
        return len([patch.old_file_path for patch in diff])

    def get_line_count(self):
        diff = self.ondisk.head.get_object().tree.diff_to_tree()
        return sum([patch.deletions for patch in diff])

    def get_author_count(self):
        commits = self.ondisk.walk(self.ondisk.head.target)
        return len(set([commit.author.email for commit in commits]))
