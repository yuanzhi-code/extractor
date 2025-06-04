from datetime import datetime, timezone


def parse_feed_datetime(dt_str: str) -> datetime:
    """
    Parse datetime string from RSS feed and convert to naive UTC datetime

    Args:
        dt_str: datetime string in RSS format (e.g. "Wed, 21 Oct 2015 07:28:00 +0000" or "Wed, 04 Jun 2025 14:15:14 GMT" or "2025-06-04T13:51:50.579Z")

    Returns:
        datetime: naive UTC datetime object
    """
    if not dt_str:
        # 如果时间字符串为空，返回当前时间
        return datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        # 首先尝试标准 RSS 格式
        dt = datetime.strptime(dt_str, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        try:
            # 尝试处理 GMT 格式
            if dt_str.endswith(" GMT"):
                dt_str = dt_str.replace(" GMT", " +0000")
                dt = datetime.strptime(dt_str, "%a, %d %b %Y %H:%M:%S %z")
            else:
                # 尝试 ISO 8601 格式
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Unsupported datetime format: {dt_str}")

    # 将时间转换为 UTC 时间，然后移除时区信息
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.replace(tzinfo=None)
