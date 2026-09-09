from datetime import datetime, date
from zoneinfo import ZoneInfo


class DateUtils:

    ARGENTINA_TZ = ZoneInfo(
        "America/Argentina/Buenos_Aires"
    )

    @classmethod
    def now_argentina(cls) -> datetime:
        return datetime.now(cls.ARGENTINA_TZ)

    @classmethod
    def today_argentina(cls) -> date:
        return cls.now_argentina().date()

    @classmethod
    def to_argentina(cls, value: datetime) -> datetime:

        if value.tzinfo is None:
            value = value.replace(tzinfo=ZoneInfo("UTC"))

        return value.astimezone(cls.ARGENTINA_TZ)