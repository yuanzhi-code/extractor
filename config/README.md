# LLM 池化配置系统说明

本目录包含LLM池化配置系统的示例文件，请根据需要复制并修改这些文件。

## 配置文件类型

### 池管理配置（推荐）

**示例文件**: `llm_pools.example.yaml`  
**实际配置文件**: `llm_pools.yaml`

这是新的池化配置系统，支持供应商声明、模型引用、池级配置等高级功能。使用YAML格式提供更好的可读性和维护性。

#### 主要特性：
- 供应商和模型分离声明
- 模型ID引用机制
- 池级别的温度、超时配置
- 独立的模型池管理
- 健康监控和断路器
- 节点到池的映射
- 多种负载均衡策略

**简化版示例**: `llm_pools_simple.example.json`  
适合快速开始使用的简化配置。

## 配置结构

新的配置采用三层结构：

### 1. 供应商声明 (providers)

首先声明所有供应商的基础信息和可用模型：

```yaml
providers:
  siliconflow:
    api_base: "https://api.siliconflow.cn/v1"
    api_key: "${SILICONFLOW_API_KEY}"
    provider: "siliconflow"
    models:
      - id: "qwen3-7b"
        model: "Qwen/Qwen3-7B-Instruct"
        weight: 1
      - id: "qwen3-14b"
        model: "Qwen/Qwen3-14B-Instruct"
        weight: 2
```

### 2. 池配置 (pools)

然后定义池，通过模型ID引用具体模型：

```yaml
pools:
  fast_pool:
    description: "快速响应池"
    models: ["qwen3-7b", "qwen3-14b"]
    load_balance_strategy: "round_robin"
    temperature: 0.0
    timeout: 10
    pool_config:
      max_retries: 3
      concurrent_limit: 20
```

### 3. 节点映射 (nodes)

最后定义节点到池的映射关系：

```yaml
nodes:
  tagger: "fast_pool"
  score: "quality_pool"
```

## 使用方法

### 1. 复制并修改示例文件

```bash
# 完整配置
cp config/llm_pools.example.yaml config/llm_pools.yaml

# 或者简化配置
cp config/llm_pools.example.yaml config/llm_pools.yaml
```

### 2. API密钥配置

配置文件中直接设置API密钥：

```yaml
api_key: "your-actual-api-key-here"
api_base: "https://api.example.com/v1"
```

### 3. 配置验证

系统会自动验证配置文件的合法性，包括：
- 供应商配置完整性
- 模型ID引用完整性
- 池配置参数范围
- 节点-池映射有效性

## 配置要求

**必须配置**: 池配置文件 (`llm_pools.yaml`)

系统现在完全基于YAML配置文件工作，所有配置包括API密钥都直接在配置文件中设置。

## 配置字段说明

### 供应商配置

```yaml
provider_name:
  api_base: "https://api.example.com/v1"  # 必需：API基础URL
  api_key: "your-api-key-here"            # 必需：API密钥
  provider: "provider_type"               # 可选：提供商类型
  models:                                 # 必需：模型列表
    - id: "model_id"                      # 必需：模型唯一ID
      model: "actual_model_name"          # 必需：实际模型名称
      weight: 1                           # 可选：权重 (0.1-100.0)
```

### 池配置

```yaml
pool_name:
  description: "池描述"                   # 可选：池描述
  models: ["model_id1", "model_id2"]     # 必需：模型ID列表
  load_balance_strategy: "round_robin"   # 可选：负载均衡策略
  temperature: 0.0                       # 可选：池级温度 (0.0-2.0)
  timeout: 30                           # 可选：池级超时 (1-300秒)
  pool_config:                         # 可选：高级池配置
    max_retries: 3                      # 最大重试次数 (1-10)
    concurrent_limit: 10                # 并发限制 (1-100)
    circuit_breaker_threshold: 5        # 断路器阈值 (1-50)
    circuit_breaker_timeout: 60         # 断路器超时 (10-3600秒)
    health_check_interval: 30            # 健康检查间隔 (10-300秒)
```

## API接口

### 配置管理

- `GET /api/llm/example-config` - 获取示例配置路径
- `POST /api/llm/validate` - 验证池配置
- `GET /api/pools/config/examples` - 获取池配置示例路径
- `POST /api/pools/config/validate` - 验证池配置

### 状态监控

- `GET /api/llm/status` - 获取LLM系统状态
- `GET /api/pools/` - 获取所有池信息
- `GET /api/pools/{pool_name}/health` - 获取池健康状态

## 配置优势

### 1. 模型复用
- 一个模型可以被多个池引用
- 不同池可以设置不同的温度、超时参数
- 减少重复配置

### 2. 灵活管理
- 池级别的温度和超时覆盖模型默认值
- 支持动态模型权重调整
- 独立的健康监控和故障隔离

### 3. 易于维护
- 供应商信息集中管理
- 模型ID引用避免重复配置
- 配置结构清晰明了

## 故障排除

1. **配置文件不存在**: 系统将无法启动，需要创建配置文件
2. **模型ID引用错误**: 检查池中引用的模型ID是否在供应商中定义
3. **配置验证失败**: 查看日志中的详细错误信息
4. **池健康检查失败**: 使用API检查具体池的健康状态
5. **API密钥错误**: 检查配置文件中的API密钥是否正确设置

## 最佳实践

1. **供应商组织**: 按提供商分组管理模型，便于维护
2. **模型命名**: 使用有意义的模型ID，如 `qwen3-7b`, `gpt4-turbo`
3. **池分层**: 根据用途创建不同池（快速池、质量池、成本池）
4. **监控配置**: 合理设置健康检查和断路器参数
5. **安全配置**: 确保配置文件权限设置正确，避免敏感信息泄露 