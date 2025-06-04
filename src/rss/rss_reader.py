import html
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import feedparser
import html2text
import requests

from src.crawl import WebContentExtractor, scrape_sync


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
        self.extractor = WebContentExtractor()

        # 设置代理
        if proxy:
            # 设置feedparser的代理
            feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    def _process_entry(self, entry: Dict) -> Dict:
        """
        处理单个RSS条目，提取并转换字段

        Args:
            entry: RSS条目字典

        Returns:
            Dict: 处理后的条目字典
        """
        entry = {
            "title": html.unescape(entry.get("title", "")),
            "feed_id": self.feed.get("id"),
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
            else:
                self.feed = feedparser.parse(url)

            if self.feed.bozo:  # 检查是否有解析错误
                logging.warning(f"解析警告: {self.feed.bozo_exception}")

                return False

            self.entries = self.feed.entries
            self.feed = self.feed.feed
            return True
        except Exception as e:
            logging.error(f"解析RSS源时发生错误: {str(e)}")
            return False

    def update_feed_info(
        self,
        property: Optional[str] = None,
        value: Optional[str] = None,
        feed_info: Optional[Dict] = None,
    ):
        """
        更新 feed 信息

        Args:
            property: 要更新的属性名
            value: 要更新的属性值
            feed_info: 完整的 feed 信息字典
        """
        if self.feed is None:
            raise ValueError("Feed is not initialized")
        if feed_info is not None:
            self.feed = feed_info
        elif property is not None and value is not None:
            self.feed[property] = value
        else:
            raise ValueError(
                "Either feed_info or both property and value must be provided"
            )

    def get_feed_info(self) -> Optional[Dict[str, str]]:
        """
        获取RSS源的基本信息

        Returns:
            Dict: 包含RSS源信息的字典
        """
        if not self.feed:
            return None
        feed_info = {
            "title": html.unescape(self.feed.get("title", "")),
            "description": html.unescape(self.feed.get("description", "")),
            "link": self.feed.get("link", ""),
            "language": self.feed.get("language", ""),
            "updated": self.feed.get("updated", ""),
        }

        if feed_info["updated"] == "" and self.entries:
            # 使用 entry 的第一条的时间作为 updated time
            feed_info["updated"] = self.entries[0].get("published")

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

        return [self._process_entry(entry) for entry in self.entries[:limit]]

    def get_entries_by_date(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        根据时间范围获取RSS条目列表

        Args:
            feed_info: RSS源信息
            start_date: 可选，起始日期时间（naive UTC）
            end_date: 可选，结束日期时间（naive UTC）

        Returns:
            List[Dict]: 符合时间范围的RSS条目列表
        """
        if not self.entries:
            return []

        filtered_entries = []
        for entry in self.entries:
            published = entry.get("published_parsed")
            if published:
                # feedparser 返回的是 time.struct_time，转换为 naive UTC datetime
                published_datetime = datetime(*published[:6])

                if (
                    start_date is None or published_datetime >= start_date
                ) and (end_date is None or published_datetime <= end_date):
                    filtered_entries.append(self._process_entry(entry))
        return filtered_entries
