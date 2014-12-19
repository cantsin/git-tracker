from models import *
from random import choice, randint
from util import clone_bare_repository
from config import ssh_public_key_path, ssh_private_key_path

# destructive!
db.drop_all()
db.create_all()

u = User("jtranovich@gmail.com", "password", "ssh-key")
u.avatar_image = 'https://avatars2.githubusercontent.com/u/3013175?v=3&s=460'
u.ssh_public_key_path = ssh_public_key_path
u.ssh_private_key_path = ssh_private_key_path
u.save()

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
    repo_path = 'git@github.com:cantsin/' + repository
    r = clone_bare_repository(u, repo_path)
    for _ in range(randint(0,5)):
        r.tags.append(choice(Tag.query.all()))
    r.save()
