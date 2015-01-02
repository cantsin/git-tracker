# pylint: disable=C0103,C0111

from models import User, Tag, UserEmail, db
from random import choice, randint
from git import GitOperations
from config import ssh_public_key_path, ssh_private_key_path

# destructive!
db.drop_all()
db.create_all()

u = User("username", "password")
u.avatar_image = 'https://avatars2.githubusercontent.com/u/3013175?v=3&s=460'
u.ssh_public_key_path = ssh_public_key_path
u.ssh_private_key_path = ssh_private_key_path
u.save()

emails = ['jtranovich@gmail.com',
          'james@openhorizonlabs.com']

for email in emails:
    ue = UserEmail(u, email).save()
    u.emails.append(ue)

tags = [('F#', 2),
        ('Data Structures', 3),
        ('Completed', 1),
        ('Public', 7),
        ('Github', 7),
        ('Code', 10),
        ('Rust', 1),
        ('Lua', 3),
        ('Hack Day', 4),
        ('Abandoned', 0),
        ('Private', 3),
        ('All', 42)]

for name, count in tags:
    t = Tag(u, name)
    t.count = count
    t.save()

repositories = ['fsharp-finger-trees',
                'glc-client',
                'dotemacs',
                'sovereign',
                'pcgen-rules',
                'ergodox-firmware',
                'rust']

for repository in repositories:
    repo_path = 'git://github.com/cantsin/' + repository
    r = GitOperations.create_repository(u, repo_path)
    for _ in range(randint(0, 5)):
        r.tags.append(choice(Tag.query.all()))
    r.save()
