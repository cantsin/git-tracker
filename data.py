# pylint: disable=C0103,C0111

from operator import attrgetter
from git import GitMixin
from sys import maxsize

class DataOperations(object):

    @staticmethod
    def get_first_updated(repositories):
        return min([repository.get_first_updated()
                    for repository in repositories],
                   default=maxsize)

    @staticmethod
    def get_last_updated(repositories):
        return max([repository.get_last_updated()
                    for repository in repositories],
                   default=0)

    @staticmethod
    def histogram(repositories, start, end):
        commits = []
        for repository in repositories:
            commits.extend(list(repository.commits_between(start, end)))
        commits.sort(key=attrgetter('commit_time'))
        return GitMixin.group_by(commits)
