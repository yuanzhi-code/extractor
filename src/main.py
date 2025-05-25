
from datetime import datetime, timedelta
import json
import logging
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
    rssReader = RssReader(config.NETWORK_PROXY)
    logging.basicConfig(level=logging.INFO)

    try:
        with open('../data/rss_sources.json', 'r', encoding='utf-8') as f:
            sources = json.load(f)
    except Exception as e:
        logging.error(f"读取配置文件失败: {str(e)}")
        return
    
    session = Session(db) 
    # 遍历所有RSS源
    for source in sources['sources']:
        logging.info(f"\n正在处理RSS源: {source['name']}")
        logging.info(f"URL: {source['url']}")
        logging.info(f"描述: {source['description']}")
        logging.info("-" * 50)

        # 添加重试机制
        max_retries = 3
        retry_delay = 5  # 秒

        for attempt in range(max_retries):
            try:
                # 解析RSS源
                if rssReader.parse_feed(source['url']):
                    # 获取RSS源信息
                    feed_info = rssReader.get_feed_info()
                    logging.info(f"Feed标题: {feed_info['title']}")
                    logging.info(f"Feed描述: {feed_info['description']}")
                    logging.info(f"Feed链接: {feed_info['link']}")
                    logging.info(f"Feed语言: {feed_info['language']}")
                    logging.info(f"最后更新: {feed_info['updated']}")
                    logging.info("-" * 50)

                    today = datetime.today()
                    start_date = datetime(today.year, today.month, 1)
                    end_date = datetime(today.year, today.month, 1) + timedelta(days=31)
                    end_date = end_date.replace(day=1) - timedelta(days=1)

                    # 获取最新的3条条目
                    # 获取本月的RSS条目
                    logging.info(f"本月的RSS条目 ({start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}):")
                    entries = rssReader.get_entries_by_date(start_date=start_date, end_date=end_date)
                    with open("output.json", "w", encoding='utf-8') as f:
                        json.dump(entries, f, ensure_ascii=False, indent=4)
                    for i, entry in enumerate(entries, 1):
                        logging.info(f"\n条目 {i}:")
                        logging.info(f"标题: {entry['title']}")
                        logging.info(f"链接: {entry['link']}")
                        logging.info(f"发布时间: {entry['published']}")
                        logging.info(f"作者: {entry['author']}")
                        logging.info(f"摘要: {entry['summary']}")
                        logging.info(f"内容: {entry['content']}")
                    break  # 成功获取数据，跳出重试循环
                else:
                    logging.warning(f"解析RSS源失败 (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        logging.warning(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
            except RequestException as e:
                logging.warning(f"网络请求错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    logging.warning(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
            except Exception as e:
                logging.error(f"发生未知错误: {str(e)}")
                break

        # 在请求之间添加延时，避免请求过于频繁
        time.sleep(2)



if __name__ == "__main__":
    main()