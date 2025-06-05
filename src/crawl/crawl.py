import asyncio
import logging
import random
import re
import time
from collections import defaultdict
from typing import Any, Optional
from urllib.parse import urlparse

import backoff
from crawl4ai import AsyncWebCrawler

# 设置日志
logger = logging.getLogger(__name__)


class AntiDetectionConfig:
    """反爬虫检测配置"""

    # User-Agent池
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
    ]

    # 请求头池
    HEADERS_POOL = [
        {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
        {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
        {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
        },
    ]

    # 延迟范围（秒）
    MIN_DELAY = 1.0
    MAX_DELAY = 3.0

    # 同域名延迟（更长）
    SAME_DOMAIN_MIN_DELAY = 3.0
    SAME_DOMAIN_MAX_DELAY = 8.0

    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0

    @classmethod
    def get_random_user_agent(cls) -> str:
        """获取随机User-Agent"""
        return random.choice(cls.USER_AGENTS)

    @classmethod
    def get_random_headers(cls) -> dict:
        """获取随机请求头"""
        return random.choice(cls.HEADERS_POOL).copy()

    @classmethod
    def get_random_delay(cls) -> float:
        """获取随机延迟时间"""
        return random.uniform(cls.MIN_DELAY, cls.MAX_DELAY)

    @classmethod
    def get_same_domain_delay(cls) -> float:
        """获取同域名的随机延迟时间（更长）"""
        return random.uniform(
            cls.SAME_DOMAIN_MIN_DELAY, cls.SAME_DOMAIN_MAX_DELAY
        )


class DomainTracker:
    """域名请求跟踪器"""

    def __init__(self):
        self.domain_last_request = defaultdict(float)
        self.domain_request_count = defaultdict(int)

    def get_domain(self, url: str) -> str:
        """从URL提取域名"""
        try:
            parsed = urlparse(url)
            return f"{parsed.netloc}"
        except Exception:
            return url

    def should_wait_for_domain(
        self, url: str, same_domain_delay: float
    ) -> float:
        """检查是否需要为特定域名等待，返回需要等待的时间"""
        domain = self.get_domain(url)
        current_time = time.time()
        last_request_time = self.domain_last_request[domain]

        if last_request_time == 0:
            # 第一次请求该域名
            self.domain_last_request[domain] = current_time
            self.domain_request_count[domain] = 1
            return 0

        time_since_last = current_time - last_request_time

        # 如果距离上次请求该域名的时间不够，需要等待
        if time_since_last < same_domain_delay:
            wait_time = same_domain_delay - time_since_last
            return wait_time

        return 0

    def update_domain_request(self, url: str):
        """更新域名请求时间"""
        domain = self.get_domain(url)
        self.domain_last_request[domain] = time.time()
        self.domain_request_count[domain] += 1

        # 记录请求统计
        count = self.domain_request_count[domain]
        if count <= 5:
            logger.info(f"域名 {domain} 第 {count} 次请求")
        elif count % 10 == 0:
            logger.info(f"域名 {domain} 已请求 {count} 次")


class WebContentExtractor:
    """网页内容提取器，专注于正文内容并转换为Markdown"""

    def __init__(
        self,
        use_anti_detection: bool = True,
        min_delay: float = 1.0,
        max_delay: float = 3.0,
        same_domain_min_delay: float = 3.0,
        same_domain_max_delay: float = 8.0,
        max_retries: int = 3,
        global_max_concurrent: int = 3,
    ):
        self.crawler = None
        self.use_anti_detection = use_anti_detection
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.same_domain_min_delay = same_domain_min_delay
        self.same_domain_max_delay = same_domain_max_delay
        self.max_retries = max_retries
        self.last_request_time = 0.0
        self.domain_tracker = DomainTracker()

        # 全局并发控制
        self.global_max_concurrent = global_max_concurrent
        self.global_semaphore = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 初始化全局并发控制信号量
        if self.use_anti_detection:
            # 启用反检测时使用更严格的并发控制
            concurrent_limit = min(self.global_max_concurrent, 2)
        else:
            concurrent_limit = self.global_max_concurrent

        self.global_semaphore = asyncio.Semaphore(concurrent_limit)
        logger.info(f"初始化全局并发限制: {concurrent_limit}")

        # 使用随机User-Agent
        user_agent = (
            AntiDetectionConfig.get_random_user_agent()
            if self.use_anti_detection
            else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        self.crawler = AsyncWebCrawler(
            verbose=True,
            headless=True,
            user_agent=user_agent,
            ignore_https_errors=True,
            java_script_enabled=True,
            load_images=False,  # 禁用图片加载
            block_resources=[
                "image",
                "media",
                "font",
                "stylesheet",
            ],  # 阻止资源加载
            # 添加额外的反检测配置
            browser_args=(
                [
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-dev-shm-usage",
                ]
                if self.use_anti_detection
                else None
            ),
        )
        await self.crawler.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)

    async def _apply_rate_limiting(self, url: str):
        """应用速率限制，包括同域名的特殊处理"""
        if not self.use_anti_detection:
            return

        current_time = time.time()

        # 1. 全局请求间隔控制
        time_since_last = current_time - self.last_request_time
        min_interval = random.uniform(self.min_delay, self.max_delay)
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            logger.debug(f"全局延迟：等待 {wait_time:.2f} 秒")
            await asyncio.sleep(wait_time)

        # 2. 同域名延迟控制（更严格）
        same_domain_delay = random.uniform(
            self.same_domain_min_delay, self.same_domain_max_delay
        )
        domain_wait_time = self.domain_tracker.should_wait_for_domain(
            url, same_domain_delay
        )

        if domain_wait_time > 0:
            domain = self.domain_tracker.get_domain(url)
            logger.info(
                f"同域名延迟：{domain} 需等待 {domain_wait_time:.2f} 秒"
            )
            await asyncio.sleep(domain_wait_time)

        # 更新请求时间
        self.last_request_time = time.time()
        self.domain_tracker.update_domain_request(url)

    def _should_retry(self, exception: Exception) -> bool:
        """判断是否应该重试"""
        # 网络相关错误需要重试
        retry_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,
            asyncio.TimeoutError,
        )

        # 检查异常类型
        if isinstance(exception, retry_exceptions):
            return True

        # 检查错误消息中的关键词
        error_msg = str(exception).lower()
        retry_keywords = [
            "timeout",
            "connection",
            "network",
            "refused",
            "reset",
            "broken pipe",
            "temporary failure",
            "502 bad gateway",
            "503 service unavailable",
            "504 gateway timeout",
            "rate limit",
            "too many requests",
        ]

        return any(keyword in error_msg for keyword in retry_keywords)

    def _should_give_up(self, exception: Exception) -> bool:
        """判断是否应该放弃重试"""
        # 这些错误不应该重试
        no_retry_exceptions = (
            PermissionError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        )

        if isinstance(exception, no_retry_exceptions):
            return True

        # 检查错误消息中的关键词
        error_msg = str(exception).lower()
        no_retry_keywords = [
            "404 not found",
            "401 unauthorized",
            "403 forbidden",
            "400 bad request",
            "file not found",
            "invalid url",
            "malformed url",
        ]

        return any(keyword in error_msg for keyword in no_retry_keywords)

    @backoff.on_exception(
        backoff.expo,
        Exception,  # 捕获所有异常
        max_tries=4,  # 最多重试3次（总共4次尝试）
        base=2,  # 指数底数
        factor=2,  # 延迟因子
        max_value=30,  # 最大延迟时间30秒
        giveup=lambda e: WebContentExtractor._should_give_up_static(
            e
        ),  # 判断是否放弃重试
        on_backoff=lambda details: logger.warning(
            f"重试 {details['tries']}/{4}: {details['exception']}, "
            f"等待 {details['wait']:.1f}s 后重试"
        ),
        on_giveup=lambda details: logger.error(
            f"达到最大重试次数 {details['tries']}, 放弃重试: {details['exception']}"
        ),
        logger=logger,
        backoff_log_level=logging.WARNING,
        giveup_log_level=logging.ERROR,
    )
    async def _crawl_with_backoff(self, url: str, **crawl_config) -> Any:
        """使用 backoff 装饰器的爬取方法"""
        # 使用全局信号量控制并发
        async with self.global_semaphore:
            # 应用速率限制（包括域名限制）
            await self._apply_rate_limiting(url)

            # 如果使用反检测，添加随机请求头
            if self.use_anti_detection:
                # 注入随机headers到crawler中
                # 注意：crawl4ai可能不直接支持per-request headers，这里作为示例
                pass

            # 将 URL 添加到爬取配置中
            crawl_config["url"] = url

            # 执行爬取
            result = await self.crawler.arun(**crawl_config)

            # 检查结果是否成功，失败则抛出异常触发重试
            if not result.success:
                error_msg = result.error_message or "Unknown crawling error"
                exception = Exception(f"爬取失败: {error_msg}")

                # 只有在判断应该重试的情况下才抛出异常
                if self._should_retry(exception):
                    raise exception
                else:
                    # 不应该重试的错误，直接返回失败结果
                    logger.warning(
                        f"不可重试的错误，直接返回失败结果: {error_msg}"
                    )
                    return result

            return result

    @staticmethod
    def _should_give_up_static(exception: Exception) -> bool:
        """静态方法版本的 _should_give_up，供 backoff 装饰器使用"""
        # 这些错误不应该重试
        no_retry_exceptions = (
            PermissionError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        )

        if isinstance(exception, no_retry_exceptions):
            return True

        # 检查错误消息中的关键词
        error_msg = str(exception).lower()
        no_retry_keywords = [
            "404 not found",
            "401 unauthorized",
            "403 forbidden",
            "400 bad request",
            "file not found",
            "invalid url",
            "malformed url",
        ]

        return any(keyword in error_msg for keyword in no_retry_keywords)

    def clean_markdown(self, markdown_content: str) -> str:
        """清理Markdown内容，移除图片和多余空行"""
        if not markdown_content:
            return ""

        # 移除图片标记 ![alt](url) 和 ![alt](url "title")
        markdown_content = re.sub(r"!\[.*?\]\(.*?\)", "", markdown_content)

        # 移除HTML图片标签
        markdown_content = re.sub(r"<img[^>]*>", "", markdown_content)

        # 移除空的链接（可能是图片链接）
        markdown_content = re.sub(r"\[\]\([^)]*\)", "", markdown_content)

        # 清理多余的空行（超过2个连续空行压缩为2个）
        markdown_content = re.sub(r"\n\s*\n\s*\n+", "\n\n", markdown_content)

        # 移除行首行尾空白
        lines = []
        for line in markdown_content.split("\n"):
            lines.append(line.rstrip())

        # 移除开头和结尾的空行
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines)

    async def extract_main_content(
        self, url: str, use_readability: bool = True
    ) -> dict[str, Any]:
        """提取网页主要内容"""
        try:
            # 爬取配置
            crawl_config = {
                "word_count_threshold": 50,  # 最少50个词
                "only_text": False,  # 保留结构用于markdown转换
                "bypass_cache": True,
                "remove_overlay_elements": True,  # 移除弹窗等覆盖元素
            }

            # 如果使用readability算法提取正文
            if use_readability:
                crawl_config["extraction_strategy"] = "readability"

            # 使用backoff装饰的方法执行爬取
            result = await self._crawl_with_backoff(url, **crawl_config)

            if not result.success:
                logger.error(f"爬取失败: {result.error_message}")
                return {
                    "success": False,
                    "error": result.error_message,
                    "content": None,
                    "title": None,
                    "url": url,
                }

            # 获取markdown内容
            markdown_content = (
                result.markdown.fit_markdown
                if hasattr(result, "markdown")
                else ""
            )

            # 如果没有markdown内容，尝试从HTML转换
            if not markdown_content and result.cleaned_html:
                markdown_content = self._html_to_markdown_simple(
                    result.cleaned_html
                )

            # 清理markdown内容
            clean_markdown = self.clean_markdown(markdown_content)

            # 提取标题
            title = self._extract_title(result)

            return {
                "success": True,
                "content": clean_markdown,
                "title": title,
                "url": url,
                "word_count": (
                    len(clean_markdown.split()) if clean_markdown else 0
                ),
                "extracted_at": (
                    result.extracted_at
                    if hasattr(result, "extracted_at")
                    else None
                ),
            }

        except Exception as e:
            logger.exception(f"提取内容时出错 {url}:")
            return {
                "success": False,
                "error": str(e),
                "content": None,
                "title": None,
                "url": url,
            }

    def _extract_title(self, result) -> Optional[str]:
        """提取页面标题"""
        # 优先使用metadata中的标题
        if hasattr(result, "metadata") and result.metadata:
            if "title" in result.metadata:
                return result.metadata["title"]
            if "og:title" in result.metadata:
                return result.metadata["og:title"]

        # 从markdown内容中提取第一个标题
        if hasattr(result, "markdown") and result.markdown:
            title_match = re.search(
                r"^#\s+(.+)$", result.markdown, re.MULTILINE
            )
            if title_match:
                return title_match.group(1).strip()

        return None

    def _html_to_markdown_simple(self, html_content: str) -> str:
        """简单的HTML到Markdown转换（备用方案）"""
        try:
            import html2text

            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True  # 忽略图片
            h.ignore_emphasis = False
            h.body_width = 0
            h.unicode_snob = True
            return h.handle(html_content)
        except ImportError:
            logger.warning("html2text未安装，返回清理后的HTML")
            # 简单清理HTML标签
            import re

            clean_text = re.sub(r"<[^>]+>", "", html_content)
            return clean_text

    def _group_urls_by_domain(self, urls: list) -> dict[str, list]:
        """按域名分组URL"""
        domain_groups = defaultdict(list)
        for url in urls:
            domain = self.domain_tracker.get_domain(url)
            domain_groups[domain].append(url)
        return dict(domain_groups)

    async def extract_multiple_urls(
        self, urls: list, max_concurrent: int = 2
    ) -> dict[str, Any]:
        """批量提取多个URL的内容，优化同域名处理"""
        # 按域名分组
        domain_groups = self._group_urls_by_domain(urls)
        logger.info(
            f"发现 {len(domain_groups)} 个不同域名：{list(domain_groups.keys())}"
        )

        # 为同域名URL添加额外延迟
        processed_results = {}

        for domain, domain_urls in domain_groups.items():
            logger.info(f"开始处理域名 {domain} 的 {len(domain_urls)} 个URL")

            # 直接处理所有URL，全局并发控制由 _crawl_with_backoff 中的信号量负责
            async def extract_single(url):
                return await self.extract_main_content(url)

            # 处理该域名下的所有URL
            tasks = [extract_single(url) for url in domain_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 整理该域名的结果
            for i, result in enumerate(results):
                url = domain_urls[i]
                if isinstance(result, Exception):
                    processed_results[url] = {
                        "success": False,
                        "error": str(result),
                        "content": None,
                        "title": None,
                        "url": url,
                    }
                else:
                    processed_results[url] = result

            # 域名之间的延迟
            if domain != list(domain_groups.keys())[-1]:  # 不是最后一个域名
                inter_domain_delay = random.uniform(2.0, 5.0)
                logger.info(
                    f"域名 {domain} 处理完成，等待 {inter_domain_delay:.2f} 秒后处理下一个域名"
                )
                await asyncio.sleep(inter_domain_delay)

        return processed_results


# 使用示例函数
async def scrape_website_to_markdown(
    url: str,
    use_readability: bool = True,
    use_anti_detection: bool = True,
    min_delay: float = 1.0,
    max_delay: float = 3.0,
    same_domain_min_delay: float = 3.0,
    same_domain_max_delay: float = 8.0,
    global_max_concurrent: int = 3,
) -> dict[str, Any]:
    """爬取单个网站并转换为Markdown"""
    async with WebContentExtractor(
        use_anti_detection=use_anti_detection,
        min_delay=min_delay,
        max_delay=max_delay,
        same_domain_min_delay=same_domain_min_delay,
        same_domain_max_delay=same_domain_max_delay,
        global_max_concurrent=global_max_concurrent,
    ) as extractor:
        result = await extractor.extract_main_content(url, use_readability)
        return result


async def scrape_multiple_websites(
    urls: list,
    max_concurrent: int = 2,
    use_anti_detection: bool = True,
    min_delay: float = 1.0,
    max_delay: float = 3.0,
    same_domain_min_delay: float = 5.0,
    same_domain_max_delay: float = 12.0,
    global_max_concurrent: int = 2,
) -> dict[str, Any]:
    """批量爬取多个网站"""
    async with WebContentExtractor(
        use_anti_detection=use_anti_detection,
        min_delay=min_delay,
        max_delay=max_delay,
        same_domain_min_delay=same_domain_min_delay,
        same_domain_max_delay=same_domain_max_delay,
        global_max_concurrent=global_max_concurrent,
    ) as extractor:
        results = await extractor.extract_multiple_urls(urls, max_concurrent)
        return results


# 简化版使用接口
async def quick_scrape(url: str, stealth_mode: bool = True) -> str:
    """快速爬取，只返回清理后的markdown内容"""
    result = await scrape_website_to_markdown(
        url, use_anti_detection=stealth_mode
    )
    if result["success"]:
        return result["content"]
    else:
        logger.error(f"爬取失败: {result['error']}")
        return ""


# 同步版本（如果需要）
def scrape_sync(url: str, use_anti_detection: bool = True) -> dict[str, Any]:
    """同步版本的爬取函数"""
    return asyncio.run(
        scrape_website_to_markdown(url, use_anti_detection=use_anti_detection)
    )


# 主函数示例
async def main():
    """主函数示例"""
    # 测试URL列表（包含同一域名的多个URL）
    test_urls = [
        "http://www.geekpark.net/news/349139",
        "http://www.geekpark.net/news/349152",
        "http://www.geekpark.net/news/349159",
        "https://example.com/page1",
        "https://example.com/page2",
        # 添加更多URL
    ]

    # 单个URL爬取
    print("=== 单个URL爬取示例（启用反检测 + backoff重试） ===")
    single_result = await scrape_website_to_markdown(
        "http://www.geekpark.net/news/349159",
        use_anti_detection=True,
        min_delay=1.5,
        max_delay=3.0,
        same_domain_min_delay=4.0,
        same_domain_max_delay=8.0,
    )

    if single_result["success"]:
        print(f"标题: {single_result['title']}")
        print(f"字数: {single_result['word_count']}")
        print(
            f"内容预览: {single_result['content'][:200]}..."
            if single_result["content"]
            else "No content"
        )
    else:
        print(f"爬取失败: {single_result['error']}")

    print(
        "\n=== 批量URL爬取示例（启用同域名延迟 + backoff重试 + 全局并发控制） ==="
    )
    # 批量URL爬取
    batch_results = await scrape_multiple_websites(
        test_urls[:4],  # 限制测试数量
        max_concurrent=1,  # 这个参数现在主要用于记录，实际并发由 global_max_concurrent 控制
        use_anti_detection=True,
        min_delay=2.0,
        max_delay=4.0,
        same_domain_min_delay=6.0,  # 同域名延迟更长
        same_domain_max_delay=15.0,
        global_max_concurrent=1,  # 全局最大并发数为1，确保严格控制
    )

    for url, result in batch_results.items():
        print(f"\nURL: {url}")
        if result["success"]:
            print(f"  标题: {result['title']}")
            print(f"  字数: {result['word_count']}")
            content_preview = (
                result["content"][:100] + "..."
                if result["content"]
                else "No content"
            )
            print(f"  内容预览: {content_preview}")
        else:
            print(f"  失败原因: {result['error']}")

    print("\n=== 快速爬取示例（隐身模式 + backoff重试） ===")
    # 快速爬取（只要内容）
    quick_content = await quick_scrape("https://example.com", stealth_mode=True)
    content_preview = (
        quick_content[:100] + "..." if quick_content else "No content"
    )
    print(f"快速爬取结果: {content_preview}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
