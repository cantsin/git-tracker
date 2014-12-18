from operator import itemgetter

import pygit2
import re

class GitException(Exception):
    pass

class GitMixin(object):

    tag_regex = re.compile('^refs/tags')
    tag_or_remote_regex = re.compile('^refs/(tags|remotes)')

    def connect_to_disk(self):
        self.ondisk = pygit2.Repository('repositories/' + self.name)

    def filter_references(self, regex):
        return filter(lambda r: regex.match(r), self.ondisk.listall_references())

    def get_tags(self):
        return self.filter_references(GitMixin.tag_regex)

    def get_branches(self):
        return self.ondisk.listall_branches(pygit2.GIT_BRANCH_REMOTE)

    def get_commits(self, count=None):
        all_commits = self.ondisk.walk(self.ondisk.head.target, pygit2.GIT_SORT_TOPOLOGICAL)
        if not count:
            return all_commits
        return list(all_commits)[:count]

    def get_latest_refs(self):
        info = list(self.filter_references(GitMixin.tag_or_remote_regex))
        refs = list(zip(info, map(self.get_commit_time, info)))
        refs.sort(key=itemgetter(1), reverse=True)
        return refs

    def get_commit_time(self, name):
        ref = self.ondisk.revparse_single(name)
        if isinstance(ref, pygit2.Tag):
            return ref.get_object().commit_time
        if isinstance(ref, pygit2.Commit):
            return ref.commit_time
        raise GitException('invalid reference: commit time could not be found.')

    def get_shorthand_of_branch(self, branch):
        return self.ondisk.lookup_branch(branch).shorthand

    def get_sha1_of_branch(self, branch):
        return str(self.ondisk.lookup_branch(branch).get_object().id)[:6]

    def get_numstat(self, commit):
        return (0, 0, 0)
