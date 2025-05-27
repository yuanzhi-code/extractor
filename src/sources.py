
from datetime import datetime, timedelta
import json
import logging
import time

from requests import RequestException
from src.config.app_config import AppConfig
from src.rss import RssReader

logger = logging.getLogger(__name__)

class Source:
    """
    Source for the RSS reader.
    """

    def __init__(self, name: str, url: str, description: str):
        self.name = name
        self.url = url
        self.description = description

    def __str__(self):
        return f"{self.name} - {self.url}"

    def to_dict(self):
        return {
            "name": self.name,
            "url": self.url,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            url=data["url"],
            description=data["description"],
        )
    
    def parse(self, rss_reader: RssReader) -> list[dict]:
        # 添加重试机制
        # TODO: introduce backoff retry
        max_retries = 3
        retry_delay = 5  # 秒
        for attempt in range(max_retries):
            try:
                if rss_reader.parse_feed(self.url):
                    feed_info = rss_reader.get_feed_info()
                    logger.info(f"Feed标题: {feed_info['title']}")
                    logger.info(f"Feed描述: {feed_info['description']}")
                    logger.info(f"Feed链接: {feed_info['link']}")
                    logger.info(f"Feed语言: {feed_info['language']}")
                    logger.info(f"最后更新: {feed_info['updated']}")
                    logger.info("-" * 50)

                    today = datetime.today()
                    start_date = datetime(today.year, today.month, 1)
                    end_date = datetime(today.year, today.month, 1) + timedelta(
                        days=31
                    )
                    end_date = end_date.replace(day=1) - timedelta(days=1)
                    logger.info(
                        f"本月的RSS条目 ({start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}):"
                    )
                    entries = rss_reader.get_entries_by_date(
                        start_date=start_date,
                        end_date=end_date,
                        feed_info=feed_info,
                    )

                    return entries

                else:
                    logger.warning(
                        f"解析RSS源失败 (尝试 {attempt + 1}/{max_retries})"
                    )
                    if attempt < max_retries - 1:
                        logging.warning(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
            except RequestException as e:
                logger.warning(
                    f"网络请求错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    logger.warning(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
            except Exception as e:
                logger.error(f"发生未知错误: {str(e)}")
                break
        # 在请求之间添加延时，避免请求过于频繁
        return []

class SourceConfig:
    def __init__(self, source_path: str):
        with open(source_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.sources = [Source.from_dict(source) for source in data["sources"]]

    @classmethod
    def from_dict(cls, data: dict):
        return [Source.from_dict(source) for source in data["sources"]]

# if __name__ == "__main__": 
def main():
    """
    entrypoint for fetch and parse source
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s",
    )
    config = AppConfig()
    rss_reader = RssReader(config.NETWORK_PROXY)
    
    source_config = SourceConfig("../data/rss_sources.json")
    for source in source_config.sources:
        source.parse(rss_reader)
        time.sleep(1)

if __name__ == "__main__":
    main()