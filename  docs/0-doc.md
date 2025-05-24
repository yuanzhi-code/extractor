# 智能内容聚合与分析平台技术方案

## 1. 项目概述

### 1.1 项目目标
构建一个基于AI驱动的内容聚合、分析和生成平台，实现从多源数据采集到智能报告生成的全流程自动化。

### 1.2 核心功能
- 多源数据聚合（Twitter、微信公众号、播客、视频）
- 智能内容分析与标签化
- 自动化日报生成
- 深度研究报告生成
- 播客内容生成

## 2. 技术架构

### 2.1 核心技术栈
- **数据采集**: RSShub + crawl4ai
- **AI处理**: litellm、langgraph (统一多模型调用)
- **音频处理**: mlx-audio
- **数据存储**: SQLite
- **深度研究**: 集成多个研究框架

### 2.2 系统架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据采集层     │    │   数据处理层     │    │   应用服务层     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ RSShub          │    │ crawl4ai        │    │ 内容分析引擎     │
│ - Twitter       │───▶│ - 内容抓取       │───▶│ - 标签分类       │
│ - 微信公众号     │    │ - Markdown转换   │    │ - 评分系统       │
│ - 播客          │    │ - 内容清洗       │    │ - 内容总结       │
│ - 视频平台       │    │                │    │                │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据存储层     │    │   AI服务层      │    │   输出生成层     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ SQLite          │    │ litellm         │    │ 日报生成器       │
│ - 内容表        │◀───│ - 多模型支持     │───▶│ 深度研究报告     │
│ - 标签表        │    │ - 统一接口       │    │ 播客生成器       │
│ - 用户表        │    │ opik监控        │    │ TTS服务         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 3. 数据库设计

### 3.1 核心表结构

#### 3.1.1 内容表 (contents)
```sql
CREATE TABLE contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type VARCHAR(50) NOT NULL,          -- 来源类型：twitter, wechat, podcast, video
    source_id VARCHAR(255) NOT NULL,           -- 原始ID
    url VARCHAR(500),                          -- 原始链接
    title TEXT,                               -- 标题
    content TEXT,                             -- 内容（markdown格式）
    raw_content TEXT,                         -- 原始内容
    author VARCHAR(255),                      -- 作者
    publish_time DATETIME,                    -- 发布时间
    fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP, -- 抓取时间
    content_hash VARCHAR(64) UNIQUE,          -- 内容哈希（用于去重）
    status INTEGER DEFAULT 0,                 -- 处理状态：0-未处理，1-已处理，2-处理失败
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_type, source_id)            -- 防止重复抓取
);

-- 创建索引
CREATE INDEX idx_contents_source ON contents(source_type, source_id);
CREATE INDEX idx_contents_hash ON contents(content_hash);
CREATE INDEX idx_contents_status ON contents(status);
CREATE INDEX idx_contents_publish_time ON contents(publish_time);
```

#### 3.1.2 标签表 (tags)
```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,        -- 标签名称
    category VARCHAR(50),                     -- 标签分类：AI, web3, tech等
    description TEXT,                         -- 标签描述
    color VARCHAR(7),                         -- 显示颜色
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 预设标签
INSERT INTO tags (name, category, color) VALUES 
('AI', 'technology', '#FF6B6B'),
('Web3', 'blockchain', '#4ECDC4'),
('机器学习', 'technology', '#45B7D1'),
('区块链', 'blockchain', '#96CEB4'),
('前端开发', 'development', '#FECA57'),
('后端开发', 'development', '#FF9FF3');
```

#### 3.1.3 内容标签关联表 (content_tags)
```sql
CREATE TABLE content_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    confidence REAL DEFAULT 0.0,             -- AI标注置信度
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE(content_id, tag_id)
);
```

#### 3.1.4 内容评分表 (content_scores)
```sql
CREATE TABLE content_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    quality_score REAL DEFAULT 0.0,          -- 质量评分 0-10
    relevance_score REAL DEFAULT 0.0,        -- 相关性评分 0-10
    popularity_score REAL DEFAULT 0.0,       -- 热度评分 0-10
    overall_score REAL DEFAULT 0.0,          -- 综合评分 0-10
    ai_summary TEXT,                          -- AI生成的摘要
    key_points JSON,                          -- 关键要点（JSON格式）
    sentiment VARCHAR(20),                    -- 情感分析：positive, negative, neutral
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
    UNIQUE(content_id)
);
```

#### 3.1.5 日报表 (daily_reports)
```sql
CREATE TABLE daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_date DATE NOT NULL UNIQUE,
    title VARCHAR(255),
    summary TEXT,                             -- 当日总结
    content TEXT,                             -- 报告内容（markdown格式）
    top_contents JSON,                        -- 热门内容列表
    tag_stats JSON,                           -- 标签统计
    total_items INTEGER DEFAULT 0,
    status INTEGER DEFAULT 0,                 -- 0-生成中，1-已完成，2-生成失败
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.6 深度研究报告表 (research_reports)
```sql
CREATE TABLE research_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,                      -- 研究查询
    content TEXT,                             -- 报告内容
    sources JSON,                             -- 引用来源
    methodology TEXT,                         -- 研究方法论
    conclusions TEXT,                         -- 结论
    status INTEGER DEFAULT 0,                 -- 0-生成中，1-已完成，2-生成失败
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.7 播客表 (podcasts)
```sql
CREATE TABLE podcasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    script TEXT,                              -- 播客脚本
    audio_file_path VARCHAR(500),             -- 音频文件路径
    duration INTEGER,                         -- 时长（秒）
    based_on_report_id INTEGER,               -- 基于的报告ID
    status INTEGER DEFAULT 0,                 -- 0-生成中，1-已完成，2-生成失败
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (based_on_report_id) REFERENCES daily_reports(id)
);
```

### 3.2 去重策略

#### 3.2.1 内容哈希去重
```python
import hashlib
import re

def generate_content_hash(title, content, author):
    """生成内容哈希用于去重"""
    # 清理和标准化内容
    clean_title = re.sub(r'\s+', ' ', title.strip().lower())
    clean_content = re.sub(r'\s+', ' ', content.strip().lower())
    
    # 组合关键信息
    combined = f"{clean_title}|{clean_content[:500]}|{author}"
    
    # 生成SHA-256哈希
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def check_duplicate(cursor, content_hash):
    """检查内容是否重复"""
    cursor.execute("SELECT id FROM contents WHERE content_hash = ?", (content_hash,))
    return cursor.fetchone() is not None
```

#### 3.2.2 相似度去重
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def similarity_deduplication(new_content, existing_contents, threshold=0.85):
    """基于相似度的去重"""
    if not existing_contents:
        return False
    
    vectorizer = TfidfVectorizer(max_features=1000)
    all_contents = existing_contents + [new_content]
    
    tfidf_matrix = vectorizer.fit_transform(all_contents)
    similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    
    return any(sim[0] > threshold for sim in similarities)
```

## 4. 核心模块设计

### 4.1 数据采集模块

#### 4.1.1 RSShub集成
```python
import requests
import asyncio
import aiohttp
from datetime import datetime

class RSShubCollector:
    def __init__(self, base_url="https://rsshub.app"):
        self.base_url = base_url
        
    async def fetch_twitter(self, username, count=20):
        """获取Twitter内容"""
        url = f"{self.base_url}/twitter/user/{username}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()
    
    async def fetch_wechat(self, account_id, count=20):
        """获取微信公众号内容"""
        url = f"{self.base_url}/wechat/mp/{account_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()
    
    async def fetch_podcast(self, feed_url):
        """获取播客内容"""
        url = f"{self.base_url}/podcast/{feed_url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()
```

#### 4.1.2 Crawl4ai集成
```python
from crawl4ai import WebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class ContentCrawler:
    def __init__(self):
        self.crawler = WebCrawler(verbose=True)
        
    async def extract_content(self, url):
        """提取网页内容为Markdown格式"""
        try:
            result = await self.crawler.arun(
                url=url,
                extraction_strategy=LLMExtractionStrategy(
                    provider="ollama/llama3",
                    api_token="your-api-token",
                    instruction="Extract the main content and convert to markdown format"
                )
            )
            return {
                'markdown': result.markdown,
                'extracted_content': result.extracted_content,
                'metadata': result.metadata
            }
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None
```

### 4.2 AI处理模块

#### 4.2.1 LiteLLM集成
```python
from litellm import completion
import json

class AIProcessor:
    def __init__(self):
        self.models = {
            'summary': 'gpt-3.5-turbo',
            'classification': 'claude-3-haiku',
            'scoring': 'gpt-4o-mini'
        }
    
    async def generate_summary(self, content):
        """生成内容摘要"""
        prompt = f"""
        请为以下内容生成一个简洁的摘要（不超过200字）：
        
        {content}
        
        摘要：
        """
        
        response = completion(
            model=self.models['summary'],
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content
    
    async def classify_content(self, content):
        """内容分类和标签生成"""
        prompt = f"""
        请分析以下内容，返回JSON格式的分类结果：
        {{
            "tags": ["标签1", "标签2", "标签3"],
            "category": "主要分类",
            "confidence": 0.85,
            "key_points": ["要点1", "要点2", "要点3"]
        }}
        
        内容：{content}
        """
        
        response = completion(
            model=self.models['classification'],
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def score_content(self, content):
        """内容评分"""
        prompt = f"""
        请对以下内容进行评分（0-10分），返回JSON格式：
        {{
            "quality_score": 8.5,
            "relevance_score": 7.0,
            "popularity_score": 6.5,
            "overall_score": 7.3,
            "reasoning": "评分理由"
        }}
        
        内容：{content}
        """
        
        response = completion(
            model=self.models['scoring'],
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.choices[0].message.content)
```

#### 4.2.2 Opik监控集成
```python
from opik import track, opik_logger

class AIMonitoring:
    def __init__(self):
        opik_logger.configure()
    
    @track
    async def track_ai_call(self, function_name, input_data, output_data):
        """跟踪AI调用"""
        return {
            'function': function_name,
            'input_size': len(str(input_data)),
            'output_size': len(str(output_data)),
            'timestamp': datetime.now().isoformat()
        }
```

### 4.3 报告生成模块

#### 4.3.1 日报生成器
```python
class DailyReportGenerator:
    def __init__(self, ai_processor, db_connection):
        self.ai_processor = ai_processor
        self.db = db_connection
    
    async def generate_daily_report(self, date):
        """生成日报"""
        # 获取当日内容
        contents = self.get_daily_contents(date)
        
        # 分析热门内容
        top_contents = self.analyze_top_contents(contents)
        
        # 生成标签统计
        tag_stats = self.generate_tag_statistics(contents)
        
        # AI生成报告内容
        report_content = await self.ai_processor.generate_report(
            contents, top_contents, tag_stats
        )
        
        # 保存报告
        self.save_daily_report(date, report_content, top_contents, tag_stats)
        
        return report_content
    
    def get_daily_contents(self, date):
        """获取指定日期的内容"""
        query = """
        SELECT c.*, cs.overall_score, cs.ai_summary
        FROM contents c
        LEFT JOIN content_scores cs ON c.id = cs.content_id
        WHERE DATE(c.publish_time) = ?
        ORDER BY cs.overall_score DESC
        """
        return self.db.execute(query, (date,)).fetchall()
```

#### 4.3.2 深度研究模块
```python
from deer_flow import DeepResearcher
from local_deep_researcher import LocalResearcher

class DeepResearchEngine:
    def __init__(self):
        self.researchers = {
            'deer_flow': DeepResearcher(),
            'local': LocalResearcher(),
            'open_deep_search': OpenDeepSearcher()
        }
    
    async def conduct_research(self, query, method='local'):
        """执行深度研究"""
        researcher = self.researchers[method]
        
        # 搜索相关内容
        search_results = await researcher.search(query)
        
        # 分析和综合信息
        analysis = await researcher.analyze(search_results)
        
        # 生成研究报告
        report = await researcher.generate_report(analysis)
        
        return {
            'query': query,
            'sources': search_results,
            'analysis': analysis,
            'report': report,
            'methodology': method
        }
```

### 4.4 播客生成模块

#### 4.4.1 播客脚本生成
```python
class PodcastGenerator:
    def __init__(self, ai_processor):
        self.ai_processor = ai_processor
    
    async def generate_podcast_script(self, report_content):
        """生成播客脚本"""
        prompt = f"""
        基于以下报告内容，生成一个10-15分钟的播客脚本。
        要求：
        1. 自然的对话风格
        2. 结构清晰（开头、主体、结尾）
        3. 包含适当的停顿和语气词
        4. 突出重点信息
        
        报告内容：{report_content}
        
        播客脚本：
        """
        
        response = await self.ai_processor.generate_content(prompt)
        return response
```

#### 4.4.2 TTS音频生成
```python
import mlx_audio
import asyncio

class TTSService:
    def __init__(self):
        self.tts_model = mlx_audio.load_tts_model()
    
    async def generate_audio(self, script, voice='default'):
        """将脚本转换为音频"""
        try:
            audio_data = await self.tts_model.synthesize(
                text=script,
                voice=voice,
                speed=1.0,
                pitch=1.0
            )
            
            return audio_data
        except Exception as e:
            print(f"TTS generation error: {e}")
            return None
    
    def save_audio(self, audio_data, file_path):
        """保存音频文件"""
        with open(file_path, 'wb') as f:
            f.write(audio_data)
```

## 5. 系统集成与工作流

### 5.1 主要工作流程
```python
class MainWorkflow:
    def __init__(self):
        self.collector = RSShubCollector()
        self.crawler = ContentCrawler()
        self.ai_processor = AIProcessor()
        self.db_manager = DatabaseManager()
        self.report_generator = DailyReportGenerator()
        self.podcast_generator = PodcastGenerator()
    
    async def daily_workflow(self):
        """每日工作流程"""
        try:
            # 1. 数据采集
            await self.collect_daily_data()
            
            # 2. 内容处理
            await self.process_new_content()
            
            # 3. 生成日报
            daily_report = await self.report_generator.generate_daily_report(
                datetime.now().date()
            )
            
            # 4. 生成播客
            await self.podcast_generator.create_podcast(daily_report)
            
            print("Daily workflow completed successfully")
            
        except Exception as e:
            print(f"Daily workflow error: {e}")
    
    async def collect_daily_data(self):
        """收集每日数据"""
        sources = [
            ('twitter', ['elonmusk', 'sama', 'karpathy']),
            ('wechat', ['tech_channel_1', 'ai_channel_2']),
            ('podcast', ['tech_podcast_feed'])
        ]
        
        for source_type, source_list in sources:
            for source in source_list:
                try:
                    data = await self.collector.fetch_data(source_type, source)
                    await self.store_data(data, source_type)
                except Exception as e:
                    print(f"Error collecting from {source}: {e}")
```

### 5.2 定时任务调度
```python
import schedule
import time
import asyncio

class TaskScheduler:
    def __init__(self, workflow):
        self.workflow = workflow
    
    def setup_schedule(self):
        """设置定时任务"""
        # 每小时采集数据
        schedule.every().hour.do(self.run_async, self.workflow.collect_daily_data)
        
        # 每天早上8点生成日报
        schedule.every().day.at("08:00").do(
            self.run_async, self.workflow.generate_daily_report
        )
        
        # 每天晚上10点生成播客
        schedule.every().day.at("22:00").do(
            self.run_async, self.workflow.generate_podcast
        )
    
    def run_async(self, coro):
        """运行异步函数"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro())
        loop.close()
    
    def start(self):
        """启动调度器"""
        while True:
            schedule.run_pending()
            time.sleep(60)
```

- 多供应商策略
- 完善的错误处理
- 持续监控和优化