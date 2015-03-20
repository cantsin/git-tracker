from apscheduler.schedulers.background import BackgroundScheduler
from models import Repository

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('interval', hours=2)
def refresh_all_repositories():
    print("running")
    for repository in Repository.query.all():
        repository.refresh()
        repository.save()
