from datetime import datetime


def parse_feed_datetime(dt_str: str) -> datetime:
    """
    Parse datetime string from RSS feed and convert to naive UTC datetime

    Args:
        dt_str: datetime string in RSS format (e.g. "Wed, 21 Oct 2015 07:28:00 +0000")

    Returns:
        datetime: naive UTC datetime object
    """
    dt = datetime.strptime(dt_str, "%a, %d %b %Y %H:%M:%S %z")
    return dt.replace(tzinfo=None)
