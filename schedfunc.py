from datetime import date, datetime, time, timedelta
from typing import Callable, Container

from loguru import logger


class SchedFunc:

    isoweekdays: Container[int]
    execution_time: time
    func: Callable
    last_executed_on: date
    last_checked_at: datetime

    def __init__(
        self,
        isoweekdays: Container[int],
        hour: int,
        minute: int,
        second: int,
        func: Callable,
    ):
        self.isoweekdays = isoweekdays
        self.execution_time = time(hour=hour, minute=minute, second=second)
        self.func = func
        self.last_executed_on = date.today() - timedelta(days=1)
        self.last_checked_at = datetime.now()

        logger.debug(
            f"New scheduler for {self.func}"
            f" on {self.isoweekdays} at {self.execution_time}."
        )

    def process(self):
        # do not execute twice on the same day
        if self.last_executed_on == date.today():
            self.last_checked_at = datetime.now()
            return

        # only execute on the specified days of the week
        today = datetime.now().isoweekday()
        if today not in self.isoweekdays:
            self.last_checked_at = datetime.now()
            return

        execute_at = datetime.combine(datetime.today(), self.execution_time)

        if self.last_checked_at < execute_at < datetime.now():
            self.last_checked_at = datetime.now()
            self.last_executed_on = date.today()
            self.func()
            self.func()
            self.func()
            self.func()
