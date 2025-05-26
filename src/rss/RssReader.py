import logging
from sqlite3 import IntegrityError
import feedparser
from datetime import datetime
from typing import List, Dict, Optional
import html
import os
import requests
import json  # 添加 json 模块导入
import html2text

from models import db
from sqlalchemy.orm import Session

from models.rss_entry import RssEntry
from models.rss_feed import RssFeed


class RssReader:
    # TODO(woxqaq): add cache for feeds and entries
    def __init__(self, proxy: Optional[str] = None):
        """
        初始化RSS阅读器

        Args:
            proxy: 代理服务器地址，格式如 'http://127.0.0.1:7890'
        """
        self.feed: Optional[Dict] = None
        self.entries: List[Dict] = []
        self.proxy: Optional[str] = proxy
        self.html2markdown = html2text.HTML2Text()
        self.html2markdown.ignore_links = False  # 保留链接
        self.html2markdown.ignore_images = False  # 保留图片

        # 设置代理
        if proxy:
            os.environ["http_proxy"] = proxy
            os.environ["https_proxy"] = proxy
            # 设置feedparser的代理
            feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    def _process_entry(self, feed_info: Dict[str, str], entry: Dict) -> Dict:
        """
        处理单个RSS条目，提取并转换字段

        Args:
            entry: RSS条目字典

        Returns:
            Dict: 处理后的条目字典
        """
        published_at = datetime.strptime(
            entry.get("published", ""), "%a, %d %b %Y %H:%M:%S %z"
        )
        entry = {
            "title": html.unescape(entry.get("title", "")),
            "feed_id": feed_info.get("id"),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "summary": html.unescape(entry.get("summary", "")),
            "author": html.unescape(entry.get("author", "")),
            "content": (
                self.html2markdown.handle(
                    html.unescape(
                        entry.get("content", [{}])[0].get("value", "")
                    )
                )
                if entry.get("content", [{}])
                else ""
            ),
        }
        with Session(db) as session:
            new_entry = entry.copy()
            new_entry.pop("published")
            new_entry["published_at"] = published_at
            try:
                session.add(RssEntry(**new_entry))
                session.commit()
            except IntegrityError:
                session.rollback()
                logging.info(f"Entry with link {entry['link']} already exists")
        return entry

    def parse_feed(self, url: str) -> bool:
        """
        解析指定URL的RSS源

        Args:
            url: RSS源的URL地址

        Returns:
            bool: 解析是否成功
        """
        try:
            # 使用requests获取内容，支持代理
            if self.proxy:
                proxies = {"http": self.proxy, "https": self.proxy}
                response = requests.get(url, proxies=proxies, timeout=10)
                self.feed = feedparser.parse(response.content)

                # 修改: 将 self.feed 转换为 JSON 字符串并写入文件
                with open("output.json", "w", encoding="utf-8") as f:
                    json.dump(self.feed, f, ensure_ascii=False, indent=4)
            else:
                self.feed = feedparser.parse(url)

            if self.feed.bozo:  # 检查是否有解析错误
                logging.warning(f"解析警告: {self.feed.bozo_exception}")

                return False

            self.entries = self.feed.entries
            return True
        except Exception as e:
            logging.error(f"解析RSS源时发生错误: {str(e)}")
            return False

    def get_feed_info(self) -> Dict[str, str]:
        """
        获取RSS源的基本信息

        Returns:
            Dict: 包含RSS源信息的字典
        """
        if not self.feed:
            return {}
        feed_info = {
            "title": html.unescape(self.feed.get("title", "")),
            "description": html.unescape(self.feed.get("description", "")),
            "link": self.feed.get("link", ""),
            "language": self.feed.get("language", ""),
            "updated": self.feed.get("updated", ""),
        }

        with Session(db) as session:
            rss_feed = RssFeed(
                title=feed_info["title"],
                description=feed_info["description"],
                link=feed_info["link"],
                language=feed_info["language"],
                updated=datetime.strptime(
                    feed_info.get("updated", ""), "%a, %d %b %Y %H:%M:%S %z"
                ),
            )
            try:
                session.add(rss_feed)
                session.commit()
                session.refresh(rss_feed)
                feed_info["id"] = rss_feed.id
            except IntegrityError:
                logging.info("RSS源已存在，跳过添加")

        return feed_info

    def get_entries(
        self, feed_info: Dict[str, str], limit: Optional[int] = None
    ) -> List[Dict]:
        """
        获取RSS条目列表

        Args:
            limit: 可选，限制返回的条目数量

        Returns:
            List[Dict]: RSS条目列表
        """
        if not self.entries:
            return []

        return [
            self._process_entry(feed_info, entry)
            for entry in self.entries[:limit]
        ]

    def get_entries_by_date(
        self,
        feed_info: Dict[str, str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        根据时间范围获取RSS条目列表

        Args:
            start_date: 可选，起始日期时间
            end_date: 可选，结束日期时间

        Returns:
            List[Dict]: 符合时间范围的RSS条目列表
        """
        if not self.entries:
            return []

        filtered_entries = []
        for entry in self.entries:
            published = entry.get("published_parsed")
            if published:
                published_datetime = datetime(*published[:6])
                if (
                    start_date is None or published_datetime >= start_date
                ) and (end_date is None or published_datetime <= end_date):
                    filtered_entries.append(
                        self._process_entry(feed_info, entry)
                    )
        return filtered_entries
