
from datetime import datetime, timedelta
import json
import time

from requests import RequestException, session
from sqlalchemy import text
from sqlalchemy.orm import Session
from config.app_config import AppConfig
from rss import RssReader
from models import db

def main():
    """
    程序入口
    """
    config = AppConfig()
    print(config.model_dump())

    rssReader = RssReader(config.NETWORK_PROXY)

    try:
        with open('../data/rss_sources.json', 'r', encoding='utf-8') as f:
            sources = json.load(f)
    except Exception as e:
        print(f"读取配置文件失败: {str(e)}")
        return
    
    session = Session(db) 
    # 遍历所有RSS源
    for source in sources['sources']:
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
                if rssReader.parse_feed(source['url']):
                    # 获取RSS源信息
                    feed_info = rssReader.get_feed_info()
                    print(f"Feed标题: {feed_info['title']}")
                    print(f"Feed描述: {feed_info['description']}")
                    print(f"Feed链接: {feed_info['link']}")
                    print(f"Feed语言: {feed_info['language']}")
                    print(f"最后更新: {feed_info['updated']}")
                    print("-" * 50)

                    today = datetime.today()
                    start_date = datetime(today.year, today.month, 1)
                    end_date = datetime(today.year, today.month, 1) + timedelta(days=31)
                    end_date = end_date.replace(day=1) - timedelta(days=1)

                    # 获取最新的3条条目
                    # 获取本月的RSS条目
                    print(f"本月的RSS条目 ({start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}):")
                    entries = rssReader.get_entries_by_date(start_date=start_date, end_date=end_date)
                    for i, entry in enumerate(entries, 1):
                        print(f"\n条目 {i}:")
                        print(f"标题: {entry['title']}")
                        print(f"链接: {entry['link']}")
                        print(f"发布时间: {entry['published']}")
                        print(f"作者: {entry['author']}")
                        print(f"摘要: {entry['summary']}")
                        print(f"内容: {entry['content']}")
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