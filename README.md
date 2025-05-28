# Extractor

An intelligent content aggregation and analysis platform that automatically collects, processes, and generates insights from multiple sources.

English | [简体中文](README_ZH.md)

## Features

### 🔄 Content Aggregation
- Multi-source data collection (Twitter, WeChat, Podcasts, Videos)
- Automatic content extraction and cleaning
- Duplicate content detection
- Support for RSS feeds

### 🤖 AI Processing
- Intelligent content tagging and categorization
- Content quality scoring
- Automated summarization

### 📊 Content Generation
- Daily report generation
- In-depth research report creation
- Podcast script generation
- Text-to-Speech conversion

## Getting Started

### Prerequisites
```bash
python >= 3.12
```

### Installation
1. Clone the repository
```bash
git clone https://github.com/yuanzhi-code/extractor.git
cd extractor
```

2. init venv and install project dependencies
```bash
uv venv && uv sync
```

3. Setup database
```bash
uv run alembic upgrade head
```

4. Configure your sources
```bash
cp data/rss_sources.json.example data/rss_sources.json
# Edit rss_sources.json with your sources
```

### Usage

TODO

## Configuration

### RSS Sources
Add your RSS sources in `data/rss_sources.json`:
```json
{
    "sources": [
        {
            "name": "Example Tech Blog",
            "url": "https://example.com/feed",
            "description": "Tech news and updates"
        }
    ]
}
```

### Environment Variables
Refer the `.env.example` and c reate a `.env` file:

To make the project run probably, you need to setup the `MODEL_PROVIDER` and relevant env showed in the `.env.example`,for example, you choose `deepseek` as model provider

```bash
MODEL_PROVIDER="deepseek"
DEEPSEEK_API_KEY="sk-xxxxxxx"
DEEPSEEK_MODEL="deepseek-chat"
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
