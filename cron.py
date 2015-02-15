from models import Repository

for repository in Repository.query.all():
    repository.refresh()
    repository.save()
