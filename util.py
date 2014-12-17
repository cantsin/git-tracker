from unicodedata import normalize

import humanize
import re

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def slugify(text, delim=b'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return delim.join(result).decode("utf-8", "strict")

def naturaltime(datetime):
    return humanize.naturaltime(datetime)

def git_url_parse(git_repo):
    """Retrieve git user repository name from the git uri."""
    # strip the protocol if applicable
    stripped = git_repo
    if '://' in git_repo:
        _, _, stripped = git_repo.partition('://')
    # obtain the repository name.
    results = stripped.split('/')
    name = results[-1]
    if not '.git' in name:
        name += '.git'
    # obtain the git user.
    git_user = 'git'
    if '@' in results[0]:
        git_user = results[0].split('@')[0]
    return git_user, name

def clone_bare_repository(user, git_repo):
    """Clone a bare repository."""
    from models import Repository, db
    from pygit2 import clone_repository, Keypair
    kind = Repository.LOCAL
    if 'github' in git_repo:
        kind = Repository.GITHUB
    if 'bitbucket' in git_repo:
        kind = Repository.BITBUCKET
    git_user, name = git_url_parse(git_repo)
    creds = Keypair(git_user, user.ssh_public_key_path, user.ssh_private_key_path, '')
    clone_repository(git_repo, 'repositories/' + name,  bare=True, credentials=creds)
    repo = Repository(user, name, git_repo, kind)
    db.session.add(repo)
    db.session.commit()
    return repo

if __name__ == "__main__":
    repos = [('git://github.com/rails/rails.git', 'git', 'rails.git'),
             ('git@github.com:cantsin/pcgen-rules', 'git', 'pcgen-rules.git'),
             ('https://github.com/cantsin/git-tracker.git', 'git', 'git-tracker.git'),
             ('ssh://git@github.com/cantsin/git-tracker.git', 'git', 'git-tracker.git'),
             ('git@github.com:cantsin/git-tracker.git', 'git', 'git-tracker.git'),
             ('git@bitbucket.org:accountname/reponame.git', 'git', 'reponame.git'),
             ('ssh://git@bitbucket.org/accountname/reponame.git', 'git', 'reponame.git'),
             ('https://foo@bitbucket.org/foo/reponame.git', 'foo', 'reponame.git'),
             ('james@foo:random/testing.git', 'james', 'testing.git')]
    for repo, git_user, name in repos:
        assert(git_url_parse(repo)==(git_user, name))
