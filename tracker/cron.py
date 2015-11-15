from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

from .models import Repository

scheduler = BackgroundScheduler(timezone=utc)

@scheduler.scheduled_job('interval', hours=2)
def refresh_all_repositories():
    for repository in Repository.query.all():
        repository.refresh()
        repository.save()
