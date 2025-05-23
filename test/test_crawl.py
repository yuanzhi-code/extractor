import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from src.crawl.crawl import main

@pytest.mark.asyncio
async def test_crawl_success():
    """测试爬虫成功情况"""
    # 模拟爬虫结果
    mock_result = AsyncMock()
    mock_result.markdown = "# 测试标题\n\n测试内容"
    
    # 模拟AsyncWebCrawler
    mock_crawler = AsyncMock()
    mock_crawler.__aenter__.return_value = mock_crawler
    mock_crawler.arun.return_value = mock_result
    
    # 使用patch模拟AsyncWebCrawler
    with patch('src.crawl.crawl.AsyncWebCrawler', return_value=mock_crawler):
        # 运行主函数
        await main()
        
        # 验证爬虫被正确调用
        mock_crawler.arun.assert_called_once_with(
            url="https://www.nbcnews.com/business"
        )

@pytest.mark.asyncio
async def test_crawl_error():
    """测试爬虫错误处理"""
    # 模拟爬虫抛出异常
    mock_crawler = AsyncMock()
    mock_crawler.__aenter__.return_value = mock_crawler
    mock_crawler.arun.side_effect = Exception("测试错误")
    
    # 使用patch模拟AsyncWebCrawler
    with patch('src.crawl.crawl.AsyncWebCrawler', return_value=mock_crawler):
        # 验证异常被正确抛出
        with pytest.raises(Exception) as exc_info:
            await main()
        assert str(exc_info.value) == "测试错误"

@pytest.mark.asyncio
async def test_crawl_empty_result():
    """测试爬虫返回空结果"""
    # 模拟空结果
    mock_result = AsyncMock()
    mock_result.markdown = ""
    
    # 模拟AsyncWebCrawler
    mock_crawler = AsyncMock()
    mock_crawler.__aenter__.return_value = mock_crawler
    mock_crawler.arun.return_value = mock_result
    
    # 使用patch模拟AsyncWebCrawler
    with patch('src.crawl.crawl.AsyncWebCrawler', return_value=mock_crawler):
        # 运行主函数
        await main()
        
        # 验证爬虫被调用
        mock_crawler.arun.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__]) 