import logging
import feedparser
from datetime import datetime
from typing import List, Dict, Optional
import html
import os
import requests
import json  # 添加 json 模块导入
import html2text


class RssReader:
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

    def _process_entry(self, entry: Dict) -> Dict:
        """
        处理单个RSS条目，提取并转换字段

        Args:
            entry: RSS条目字典

        Returns:
            Dict: 处理后的条目字典
        """
        return {
            "title": html.unescape(entry.get("title", "")),
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
        return {
            "title": html.unescape(self.feed.get("title", "")),
            "description": html.unescape(self.feed.get("description", "")),
            "link": self.feed.get("link", ""),
            "language": self.feed.get("language", ""),
            "updated": self.feed.get("updated", ""),
        }

    def get_entries(self, limit: Optional[int] = None) -> List[Dict]:
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
                    filtered_entries.append(self._process_entry(entry))
        return filtered_entries


# def main():
#     """
#     测试RSS阅读器功能
#     """
#     import json
#     import time
#     from requests.exceptions import RequestException
#     from datetime import datetime, timedelta

#     # 设置代理
#     proxy = "http://127.0.0.1:7897"  # 根据您的实际代理地址修改

#     # 读取RSS源配置
#     try:
#         with open('data/rss_sources.json', 'r', encoding='utf-8') as f:
#             config = json.load(f)
#     except Exception as e:
#         print(f"读取配置文件失败: {str(e)}")
#         return

#     # 创建RSS阅读器实例，传入代理设置
#     reader = RssReader(proxy=proxy)

#     # 遍历所有RSS源
#     for source in config['sources']:
#         print(f"\n正在处理RSS源: {source['name']}")
#         print(f"URL: {source['url']}")
#         print(f"描述: {source['description']}")
#         print("-" * 50)

#         # 添加重试机制
#         max_retries = 3
#         retry_delay = 5  # 秒

#         for attempt in range(max_retries):
#             try:
#                 # 解析RSS源
#                 if reader.parse_feed(source['url']):
#                     # 获取RSS源信息
#                     feed_info = reader.get_feed_info()
#                     print(f"Feed标题: {feed_info['title']}")
#                     print(f"Feed描述: {feed_info['description']}")
#                     print(f"Feed链接: {feed_info['link']}")
#                     print(f"Feed语言: {feed_info['language']}")
#                     print(f"最后更新: {feed_info['updated']}")
#                     print("-" * 50)

#                     # 获取本月的起始日期和结束日期
#                     today = datetime.today()
#                     start_date = datetime(today.year, today.month, 1)
#                     end_date = datetime(today.year, today.month, 1) + timedelta(days=31)
#                     end_date = end_date.replace(day=1) - timedelta(days=1)

#                     # 获取本月的RSS条目
#                     print(f"本月的RSS条目 ({start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}):")
#                     entries = reader.get_entries_by_date(start_date=start_date, end_date=end_date)
#                     for i, entry in enumerate(entries, 1):
#                         print(f"\n条目 {i}:")
#                         print(f"标题: {entry['title']}")
#                         print(f"链接: {entry['link']}")
#                         print(f"发布时间: {entry['published']}")
#                         print(f"作者: {entry['author']}")
#                         print(f"摘要: {entry['summary']}")
#                         print(f"内容: {entry['content']}")
#                     break  # 成功获取数据，跳出重试循环
#                 else:
#                     print(f"解析RSS源失败 (尝试 {attempt + 1}/{max_retries})")
#                     if attempt < max_retries - 1:
#                         print(f"等待 {retry_delay} 秒后重试...")
#                         time.sleep(retry_delay)
#             except RequestException as e:
#                 print(f"网络请求错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
#                 if attempt < max_retries - 1:
#                     print(f"等待 {retry_delay} 秒后重试...")
#                     time.sleep(retry_delay)
#             except Exception as e:
#                 print(f"发生未知错误: {str(e)}")
#                 break

#         # 在请求之间添加延时，避免请求过于频繁
#         time.sleep(2)

# if __name__ == "__main__":
#     main()
