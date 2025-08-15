import datetime
import statistics


class TimeUtils:

    @staticmethod
    def now_utc() -> datetime.datetime:
        """Current UTC time (with time zone)"""
        return datetime.datetime.now(datetime.timezone.utc)
