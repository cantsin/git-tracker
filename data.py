# pylint: disable=C0103,C0111

from operator import attrgetter
from git import GitMixin
from sys import maxsize

class DataOperations(object):

    def __init__(self, repositories, start=None, end=None):
        if start:
            self.first_updated = int(start)
        else:
            values = [repository.get_first_updated() for repository in repositories]
            self.first_updated = min(values, default=maxsize)

        if end:
            self.last_updated = int(end)
        else:
            values = [repository.get_last_updated() for repository in repositories]
            self.last_updated = max(values, default=0)

        # calculate histogram.
        commits = []
        for repository in repositories:
            commits.extend(list(repository.commits_between(self.first_updated, self.last_updated)))
        commits.sort(key=attrgetter('commit_time'))
        self.histogram = GitMixin.group_by(commits)
