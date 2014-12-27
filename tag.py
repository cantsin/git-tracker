# pylint: disable=C0103,C0111

from sys import maxsize

class TagDataMixin(object):

    def get_first_updated(self):
        return min([repository.get_first_updated()
                    for repository in self.repositories],
                   default=maxsize)

    def get_last_updated(self):
        return max([repository.get_last_updated()
                    for repository in self.repositories],
                   default=0)

    def histogram(self, start, end):
        pass
