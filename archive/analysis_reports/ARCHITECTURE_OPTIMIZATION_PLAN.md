# 系统架构优化实施计划

**基于架构分析报告的优化方案**

## Phase 1: 性能和安全（立即实施）

### 1. LLM 异步调用改造 ✅

**状态**: 已部分实施  
**位置**: `modules/ai_gateway/gateway.py`  
**检查项**:
- [x] Gateway 使用 async def
- [ ] 所有 Provider 使用异步客户端
- [ ] 移除 `asyncio.to_thread`

**TODO**:
```python
# 需要改造所有 Provider 使用异步客户端
# modules/ai_gateway/providers/*.py

# DeepSeek Provider
from openai import AsyncOpenAI  # 替换同步客户端

class DeepSeekProviderAsync(BaseLLMProvider):
    def __init__(self, config: dict):
        self.client = AsyncOpenAI(
            api_key=config['api_key'],
            base_url="https://api.deepseek.com/v1"
        )
    
    async def generate(self, messages: List[Dict], **kwargs) -> str:
        # 直接异步调用，无需 asyncio.to_thread
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content
```

### 2. 离线队列容量限制 ✅

**状态**: 未实施  
**位置**: `client/cache/local_cache.py`  
**当前问题**: 无容量限制，可能无限增长

**TODO**:
```python
class LocalCacheV2:
    def __init__(self, cache_dir: str = "client_cache", max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size
        # ...
    
    def add_to_offline_queue(self, message: dict):
        queue = self._load_offline_queue()
        
        # 容量限制 (FIFO)
        if len(queue) >= self.max_queue_size:
            logger.warning(f"离线队列已满 ({self.max_queue_size})，丢弃最旧的消息")
            queue = queue[-(self.max_queue_size - 1):]
        
        queue.append(message)
        self._save_offline_queue_atomic(queue)
    
    def _save_offline_queue_atomic(self, queue: List[dict]):
        \"\"\"原子性保存离线队列\"\"\"
        temp_file = self.offline_queue_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)
        temp_file.replace(self.offline_queue_file)  # 原子替换
```

### 3. 统一密钥管理 ✅

**状态**: 已实施  
**位置**: `set_env.sh`, `.env_example`  
**检查项**:
- [x] 所有密钥使用环境变量
- [x] `.gitignore` 包含 `.env`
- [x] 提供 `.env` 示例文件

**建议**: 添加密钥验证脚本

```python
# scripts/validate_env.py
import os
import sys

REQUIRED_KEYS = [
    'QWEN_API_KEY',
    'GLM_API_KEY',
    'JWT_SECRET_KEY',
    'ERP_USERNAME',
    'ERP_PASSWORD'
]

OPTIONAL_KEYS = [
    'DEEPSEEK_API_KEY',
    'OPENAI_API_KEY',
    'CLAUDE_API_KEY'
]

def validate_env():
    missing = []
    for key in REQUIRED_KEYS:
        if not os.getenv(key):
            missing.append(key)
    
    if missing:
        print(f"❌ 缺少必需的环境变量:")
        for key in missing:
            print(f"  - {key}")
        print(f"\n请运行: source set_env.sh")
        sys.exit(1)
    
    print("✅ 所有必需的环境变量已设置")
    
    optional_missing = [k for k in OPTIONAL_KEYS if not os.getenv(k)]
    if optional_missing:
        print(f"\n⚠️  未设置的可选环境变量:")
        for key in optional_missing:
            print(f"  - {key}")

if __name__ == "__main__":
    validate_env()
```

### 4. SQLite WAL 模式优化 ✅

**状态**: 未实施  
**位置**: `modules/storage/db.py`  
**当前问题**: 默认模式，写操作锁表

**TODO**:
```python
class Database:
    async def connect(self):
        self.conn = await aiosqlite.connect(self.db_path)
        
        # 启用 WAL 模式
        await self.conn.execute('PRAGMA journal_mode=WAL')
        
        # 其他优化
        await self.conn.execute('PRAGMA synchronous=NORMAL')  # 提高写入性能
        await self.conn.execute('PRAGMA cache_size=10000')    # 增大缓存
        await self.conn.execute('PRAGMA temp_store=MEMORY')   # 临时表在内存
        
        logger.info("✅ SQLite WAL 模式已启用")
```

## Phase 2: 成本和监控（短期）

### 1. 成本追踪和预警系统

**TODO**: 创建 `modules/monitoring/cost_tracker.py`

```python
import redis
from datetime import datetime
from typing import Dict

class CostTracker:
    # 价格表 (每千tokens，单位：元)
    PRICING = {
        'qwen-max': {'input': 0.04, 'output': 0.12},
        'qwen-plus': {'input': 0.02, 'output': 0.06},
        'glm-4': {'input': 0.05, 'output': 0.05},
        'deepseek-chat': {'input': 0.001, 'output': 0.002},
        'gpt-4': {'input': 0.21, 'output': 0.42},
        'gpt-3.5-turbo': {'input': 0.003, 'output': 0.006},
    }
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.daily_budget = 100.0  # 每日预算 100元
    
    async def track_call(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        user_id: str = "system"
    ) -> Dict:
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 计算成本
        pricing = self.PRICING.get(model, {'input': 0.01, 'output': 0.02})
        cost = (
            input_tokens / 1000 * pricing['input'] +
            output_tokens / 1000 * pricing['output']
        )
        
        # 更新成本统计
        self.redis.incrbyfloat(f"cost:total:{today}", cost)
        self.redis.incrbyfloat(f"cost:provider:{provider}:{today}", cost)
        self.redis.incrbyfloat(f"cost:model:{model}:{today}", cost)
        self.redis.incrbyfloat(f"cost:user:{user_id}:{today}", cost)
        
        # 更新调用次数
        self.redis.incr(f"calls:total:{today}")
        self.redis.incr(f"calls:model:{model}:{today}")
        
        # 检查预算
        total_cost = float(self.redis.get(f"cost:total:{today}") or 0)
        
        result = {
            "cost": round(cost, 4),
            "total_today": round(total_cost, 2),
            "budget_remaining": round(self.daily_budget - total_cost, 2),
            "budget_used_pct": round(total_cost / self.daily_budget * 100, 1)
        }
        
        # 预算预警
        if total_cost > self.daily_budget * 0.8:
            await self._send_alert(f"⚠️ 今日成本已达 {result['budget_used_pct']}%")
        
        if total_cost > self.daily_budget:
            await self._send_alert(f"❌ 今日成本超预算！当前: {total_cost}元，预算: {self.daily_budget}元")
        
        return result
    
    async def _send_alert(self, message: str):
        # TODO: 集成钉钉/邮件/短信告警
        logger.warning(message)
    
    async def get_daily_report(self, date: str = None) -> Dict:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        total_cost = float(self.redis.get(f"cost:total:{date}") or 0)
        total_calls = int(self.redis.get(f"calls:total:{date}") or 0)
        
        return {
            "date": date,
            "total_cost": round(total_cost, 2),
            "total_calls": total_calls,
            "avg_cost_per_call": round(total_cost / total_calls, 4) if total_calls > 0 else 0,
            "budget": self.daily_budget,
            "budget_remaining": round(self.daily_budget - total_cost, 2),
            "budget_used_pct": round(total_cost / self.daily_budget * 100, 1)
        }
```

### 2. 基础监控指标 (RED)

**TODO**: 创建 `modules/monitoring/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# HTTP 请求指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# LLM 调用指标
llm_calls_total = Counter(
    'llm_calls_total',
    'Total LLM calls',
    ['provider', 'model', 'status']
)

llm_call_duration_seconds = Histogram(
    'llm_call_duration_seconds',
    'LLM call duration',
    ['provider', 'model']
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total LLM tokens',
    ['provider', 'model', 'type']  # type: input/output
)

llm_cost_total = Counter(
    'llm_cost_total',
    'Total LLM cost in CNY',
    ['provider', 'model']
)

# 缓存指标
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# 客户端指标
active_clients = Gauge(
    'active_clients',
    'Number of active clients'
)

offline_queue_size = Gauge(
    'offline_queue_size',
    'Size of offline message queue',
    ['client_id']
)

# FastAPI 中间件
from fastapi import Request
import time

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

### 3. 监控面板

**TODO**: 创建 Grafana 仪表盘配置

```json
{
  "dashboard": {
    "title": "WeChat AI 客服系统监控",
    "panels": [
      {
        "title": "HTTP 请求速率 (QPS)",
        "targets": [{
          "expr": "rate(http_requests_total[1m])"
        }]
      },
      {
        "title": "HTTP 请求延迟 (P95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, http_request_duration_seconds)"
        }]
      },
      {
        "title": "LLM 调用成本 (今日)",
        "targets": [{
          "expr": "sum(llm_cost_total)"
        }]
      },
      {
        "title": "缓存命中率",
        "targets": [{
          "expr": "rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))"
        }]
      },
      {
        "title": "活跃客户端数",
        "targets": [{
          "expr": "active_clients"
        }]
      }
    ]
  }
}
```

## Phase 3: 数据库迁移（中期）

### 1. PostgreSQL 配置

**TODO**: 创建 `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: wxauto
      POSTGRES_USER: wxauto
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init_pg.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    command: >
      postgres
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  postgres_data:
  redis_data:
```

### 2. 数据迁移脚本

**TODO**: 创建 `scripts/migrate_to_postgres.py`

```python
import asyncio
import aiosqlite
import asyncpg
from tqdm import tqdm

async def migrate_sqlite_to_postgres():
    # 连接 SQLite
    sqlite_conn = await aiosqlite.connect("storage/wxauto.db")
    
    # 连接 PostgreSQL
    pg_conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='wxauto',
        password=os.getenv('POSTGRES_PASSWORD'),
        database='wxauto'
    )
    
    # 迁移客户表
    print("迁移客户表...")
    async with sqlite_conn.execute("SELECT * FROM customers") as cursor:
        rows = await cursor.fetchall()
        for row in tqdm(rows):
            await pg_conn.execute(
                """INSERT INTO customers (id, name, phone, created_at, ...)
                   VALUES ($1, $2, $3, $4, ...)""",
                *row
            )
    
    # 迁移消息表
    print("迁移消息表...")
    # ...类似处理
    
    print("✅ 数据迁移完成")

if __name__ == "__main__":
    asyncio.run(migrate_sqlite_to_postgres())
```

## 实施检查清单

### Phase 1 (本次完成)
- [ ] LLM 异步调用改造
- [ ] 离线队列容量限制
- [x] 统一密钥管理
- [ ] SQLite WAL 模式
- [ ] 环境变量验证脚本

### Phase 2 (下次实施)
- [ ] 成本追踪系统
- [ ] Prometheus 指标
- [ ] Grafana 仪表盘
- [ ] Redis 部署
- [ ] 告警系统

### Phase 3 (长期计划)
- [ ] PostgreSQL 部署
- [ ] 数据迁移脚本
- [ ] 连接池配置
- [ ] 查询优化
- [ ] 回滚预案

## 文档更新清单
- [x] 系统架构分析报告
- [ ] Phase 1 优化实施文档
- [ ] 性能测试报告
- [ ] 运维手册更新
- [ ] README 更新

---

**最后更新**: 2025-01-20
**负责人**: AI Architect

