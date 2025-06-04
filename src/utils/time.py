from datetime import datetime


def parse_feed_datetime(dt_str: str) -> datetime:
    """
    Parse datetime string from RSS feed and convert to naive UTC datetime

    Args:
        dt_str: datetime string in RSS format (e.g. "Wed, 21 Oct 2015 07:28:00 +0000" or "Wed, 04 Jun 2025 14:15:14 GMT" or "2025-06-04T13:51:50.579Z")

    Returns:
        datetime: naive UTC datetime object
    """
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
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Unsupported datetime format: {dt_str}")
    
    return dt.replace(tzinfo=None)
