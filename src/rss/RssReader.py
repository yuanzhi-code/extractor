import feedparser
from datetime import datetime
from typing import List, Dict, Optional
import html
from requests.exceptions import RequestException
import os
import requests

class RssReader:
    def __init__(self, proxy: Optional[str] = None):
        """
        初始化RSS阅读器
        
        Args:
            proxy: 代理服务器地址，格式如 'http://127.0.0.1:7890'
        """
        self.feed = None
        self.entries = []
        self.proxy = proxy
        
        # 设置代理
        if proxy:
            os.environ['http_proxy'] = proxy
            os.environ['https_proxy'] = proxy
            # 设置feedparser的代理
            feedparser.PREFERRED_XML_PARSERS = ['lxml']
            feedparser.USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
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
                proxies = {
                    'http': self.proxy,
                    'https': self.proxy
                }
                response = requests.get(url, proxies=proxies, timeout=10)
                self.feed = feedparser.parse(response.content)
            else:
                self.feed = feedparser.parse(url)
                
            if self.feed.bozo:  # 检查是否有解析错误
                print(f"解析警告: {self.feed.bozo_exception}")
                return False
                
            self.entries = self.feed.entries
            return True
        except Exception as e:
            print(f"解析RSS源时发生错误: {str(e)}")
            return False
            
    def get_feed_info(self) -> Dict:
        """
        获取RSS源的基本信息
        
        Returns:
            Dict: 包含RSS源信息的字典
        """
        if not self.feed:
            return {}
            
        return {
            'title': html.unescape(self.feed.feed.get('title', '')),
            'description': html.unescape(self.feed.feed.get('description', '')),
            'link': self.feed.feed.get('link', ''),
            'language': self.feed.feed.get('language', ''),
            'updated': self.feed.feed.get('updated', '')
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
            
        entries = []
        for entry in self.entries[:limit]:
            entry_dict = {
                'title': html.unescape(entry.get('title', '')),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'summary': html.unescape(entry.get('summary', '')),
                'author': html.unescape(entry.get('author', ''))
            }
            entries.append(entry_dict)
            
        return entries
        
    def get_latest_entry(self) -> Optional[Dict]:
        """
        获取最新的RSS条目
        
        Returns:
            Optional[Dict]: 最新的RSS条目，如果没有条目则返回None
        """
        if not self.entries:
            return None
            
        latest = self.entries[0]
        return {
            'title': html.unescape(latest.get('title', '')),
            'link': latest.get('link', ''),
            'published': latest.get('published', ''),
            'summary': html.unescape(latest.get('summary', '')),
            'author': html.unescape(latest.get('author', ''))
        }

def main():
    """
    测试RSS阅读器功能
    """
    import json
    import time
    from requests.exceptions import RequestException
    
    # 设置代理
    proxy = "http://127.0.0.1:7897"  # 根据您的实际代理地址修改
    
    # 读取RSS源配置
    try:
        with open('data/rss_sources.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"读取配置文件失败: {str(e)}")
        return
        
    # 创建RSS阅读器实例，传入代理设置
    reader = RssReader(proxy=proxy)
    
    # 遍历所有RSS源
    for source in config['sources']:
        print(f"\n正在处理RSS源: {source['name']}")
        print(f"URL: {source['url']}")
        print(f"描述: {source['description']}")
        print("-" * 50)
        
        # 添加重试机制
        max_retries = 3
        retry_delay = 5  # 秒
        
        for attempt in range(max_retries):
            try:
                # 解析RSS源
                if reader.parse_feed(source['url']):
                    # 获取RSS源信息
                    feed_info = reader.get_feed_info()
                    print(f"Feed标题: {feed_info['title']}")
                    print(f"Feed描述: {feed_info['description']}")
                    print(f"Feed链接: {feed_info['link']}")
                    print(f"Feed语言: {feed_info['language']}")
                    print(f"最后更新: {feed_info['updated']}")
                    print("-" * 50)
                    
                    # 获取最新的3条条目
                    print("最新3条条目:")
                    entries = reader.get_entries(limit=3)
                    for i, entry in enumerate(entries, 1):
                        print(f"\n条目 {i}:")
                        print(f"标题: {entry['title']}")
                        print(f"链接: {entry['link']}")
                        print(f"发布时间: {entry['published']}")
                        print(f"作者: {entry['author']}")
                        print(f"摘要: {entry['summary']}")
                    break  # 成功获取数据，跳出重试循环
                else:
                    print(f"解析RSS源失败 (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        print(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
            except RequestException as e:
                print(f"网络请求错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    print(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
            except Exception as e:
                print(f"发生未知错误: {str(e)}")
                break
                
        # 在请求之间添加延时，避免请求过于频繁
        time.sleep(2)
        
if __name__ == "__main__":
    main()
