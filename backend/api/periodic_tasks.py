from .tasks import update_deposits_and_withdrawals


def periodically_run_job():
    """This task will be run by APScheduler."""
    update_deposits_and_withdrawals.send()
