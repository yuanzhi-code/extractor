# Extractor

一个智能的内容聚合和分析平台，能够自动从多个来源收集、处理数据并生成不同的摘要形式。

[English](README.md) | 简体中文

## 功能特点

### 🔄 内容聚合
- 多源数据采集（Twitter、微信、播客、视频）
- 自动内容提取和清洗
- 重复内容检测
- RSS 订阅源支持

### 🤖 AI 处理
- 智能内容标签和分类
- 内容质量评分
- 自动摘要生成

### 📊 内容生成
- 每日报告生成
- 深度研究报告
- 播客脚本生成
- 文字转语音转换

## 快速开始

### 环境要求
```bash
python >= 3.12
```

### 安装步骤
1. 克隆仓库
```bash
git clone https://github.com/yourusername/extractor.git
cd extractor
```

2. 安装依赖
```bash
pip install -e .
```

3. 配置数据源
```bash
cp data/rss_sources.json.example data/rss_sources.json
# 编辑 rss_sources.json 添加你的数据源
```

### 使用方法

TODO

## 配置说明

### RSS 数据源
在 `data/rss_sources.json` 中添加你的 RSS 源：
```json
{
    "sources": [
        {
            "name": "示例科技博客",
            "url": "https://example.com/feed",
            "description": "科技新闻和更新"
        }
    ]
}
```

### 环境变量
参考 `.src/.env.example` 创建 `.env` 文件：
```
NETWORK_PROXY=http://your-proxy:port  
...
```

## 参与贡献

1. Fork 本仓库
2. 创建你的特性分支
3. 提交你的改动
4. 推送到分支
5. 提交 Pull Request
