from apscheduler.schedulers.background import BlockingScheduler
from django.core.management.base import BaseCommand, CommandError
from backend.api.periodic_tasks import periodically_run_job
from pytz import UTC


class Command(BaseCommand):
    help = 'Run periodic tasks'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Preparing scheduler'))
        scheduler = BlockingScheduler(timezone=UTC)
        scheduler.add_job(periodically_run_job, 'interval', minutes=1)
        self.stdout.write(self.style.NOTICE('Start scheduler'))
        scheduler.start()
