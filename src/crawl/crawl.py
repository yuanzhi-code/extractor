import asyncio
import logging
import re
from typing import Any, Dict, Optional

from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

# 设置日志
logger = logging.getLogger(__name__)


class WebContentExtractor:
    """网页内容提取器，专注于正文内容并转换为Markdown"""

    def __init__(self):
        self.crawler = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.crawler = AsyncWebCrawler(
            verbose=True,
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            ignore_https_errors=True,
            java_script_enabled=True,
            load_images=False,  # 禁用图片加载
            block_resources=[
                "image",
                "media",
                "font",
                "stylesheet",
            ],  # 阻止资源加载
        )
        await self.crawler.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)

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
    ) -> Dict[str, Any]:
        """提取网页主要内容"""
        try:
            # 爬取配置
            crawl_config = {
                "url": url,
                "word_count_threshold": 50,  # 最少50个词
                "only_text": False,  # 保留结构用于markdown转换
                "bypass_cache": True,
                "remove_overlay_elements": True,  # 移除弹窗等覆盖元素
            }

            # 如果使用readability算法提取正文
            if use_readability:
                crawl_config["extraction_strategy"] = "readability"

            # 执行爬取
            result = await self.crawler.arun(**crawl_config)

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
            logger.error(f"提取内容时出错 {url}: {str(e)}")
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

    async def extract_multiple_urls(
        self, urls: list, max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """批量提取多个URL的内容"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_single(url):
            async with semaphore:
                return await self.extract_main_content(url)

        tasks = [extract_single(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        processed_results = {}
        for i, result in enumerate(results):
            url = urls[i]
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

        return processed_results


# 使用示例函数
async def scrape_website_to_markdown(
    url: str, use_readability: bool = True
) -> Dict[str, Any]:
    """爬取单个网站并转换为Markdown"""
    async with WebContentExtractor() as extractor:
        result = await extractor.extract_main_content(url, use_readability)
        return result


async def scrape_multiple_websites(
    urls: list, max_concurrent: int = 3
) -> Dict[str, Any]:
    """批量爬取多个网站"""
    async with WebContentExtractor() as extractor:
        results = await extractor.extract_multiple_urls(urls, max_concurrent)
        return results


# 简化版使用接口
async def quick_scrape(url: str) -> str:
    """快速爬取，只返回清理后的markdown内容"""
    result = await scrape_website_to_markdown(url)
    if result["success"]:
        return result["content"]
    else:
        logger.error(f"爬取失败: {result['error']}")
        return ""


# 同步版本（如果需要）
def scrape_sync(url: str) -> Dict[str, Any]:
    """同步版本的爬取函数"""
    return asyncio.run(scrape_website_to_markdown(url))


# 主函数示例
async def main():
    """主函数示例"""
    # 测试URL列表
    test_urls = [
        "http://www.geekpark.net/news/349139",
        "http://www.geekpark.net/news/349152",
        # 添加更多URL
    ]

    # 单个URL爬取
    print("=== 单个URL爬取示例 ===")
    single_result = await scrape_website_to_markdown(
        "http://www.geekpark.net/news/349159"
    )

    if single_result["success"]:
        print(f"标题: {single_result['title']}")
        print(f"字数: {single_result['word_count']}")
        print(f"内容预览: {single_result['content']}")
    else:
        print(f"爬取失败: {single_result['error']}")

    print("\n=== 批量URL爬取示例 ===")
    # 批量URL爬取
    batch_results = await scrape_multiple_websites(
        test_urls[:2]
    )  # 限制测试数量

    for url, result in batch_results.items():
        print(f"\nURL: {url}")
        if result["success"]:
            print(f"  标题: {result['title']}")
            print(f"  字数: {result['word_count']}")
            print(
                f"  内容预览: {result['content'] if result['content'] else 'No content'}..."
            )
        else:
            print(f"  失败原因: {result['error']}")

    print("\n=== 快速爬取示例 ===")
    # 快速爬取（只要内容）
    quick_content = await quick_scrape("https://example.com")
    print(
        f"快速爬取结果: {quick_content if quick_content else 'No content'}..."
    )


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
