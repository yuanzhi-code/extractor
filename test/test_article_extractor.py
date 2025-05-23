import pytest
from bs4 import BeautifulSoup
import requests
from unittest.mock import patch, Mock

def test_extract_article():
    """测试文章提取功能"""
    # 模拟HTML内容
    mock_html = """
    <html>
        <body>
            <h1>测试标题</h1>
            <article>
                <p>第一段内容</p>
                <h2>小标题</h2>
                <p>第二段内容</p>
            </article>
            <time>2024-03-21</time>
            <a class="author">测试作者</a>
        </body>
    </html>
    """
    
    # 模拟requests.get的响应
    mock_response = Mock()
    mock_response.text = mock_html
    mock_response.raise_for_status = Mock()
    
    # 使用patch模拟requests.get
    with patch('requests.get', return_value=mock_response):
        from article_extractor import extract_article
        
        # 测试提取功能
        result = extract_article("https://example.com/test")
        
        # 验证结果
        assert result['title'] == "测试标题"
        assert "第一段内容" in result['content']
        assert "第二段内容" in result['content']
        assert result['published_date'] == "2024-03-21"
        assert result['author'] == "测试作者"
        assert result['url'] == "https://example.com/test"

def test_extract_article_error_handling():
    """测试错误处理"""
    # 模拟请求失败
    with patch('requests.get', side_effect=requests.RequestException("测试错误")):
        from article_extractor import extract_article
        
        # 测试错误处理
        result = extract_article("https://example.com/test")
        assert result == {}

def test_extract_article_missing_elements():
    """测试缺少元素的情况"""
    # 模拟不完整的HTML
    mock_html = """
    <html>
        <body>
            <p>只有内容</p>
        </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.text = mock_html
    mock_response.raise_for_status = Mock()
    
    with patch('requests.get', return_value=mock_response):
        from article_extractor import extract_article
        
        result = extract_article("https://example.com/test")
        
        # 验证结果
        assert result['title'] == ""
        assert "只有内容" in result['content']
        assert result['published_date'] == ""
        assert result['author'] == ""
        assert result['url'] == "https://example.com/test"

if __name__ == "__main__":
    pytest.main([__file__]) 