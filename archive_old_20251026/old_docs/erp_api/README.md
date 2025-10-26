# 智邦国际 ERP OpenAPI 集成文档

## 📖 概述

本目录用于存放智邦国际 ERP 系统的 OpenAPI 文档和集成代码。

**官方文档地址**: http://ls1.jmt.ink:46088/sysn/view/OpenApi/help.ashx （需登录）

---

## 📂 文件说明

- `智邦国际ERP_OpenAPI文档.md` - API 文档（Markdown 格式）
- `智邦国际ERP_OpenAPI文档.html` - API 文档（HTML 原始格式）
- `erp_integration.py` - ERP 集成代码（待创建）
- `README.md` - 本文档

---

## 🚀 快速获取文档

### 方法一：使用抓取工具（推荐）

```bash
# 安装依赖
pip install requests beautifulsoup4

# 运行工具
python tools/fetch_erp_docs.py
```

**步骤**：
1. 在 Chrome 中登录 ERP 系统
2. 打开开发者工具（F12）→ Network 标签
3. 刷新页面，找到任意请求
4. 复制 Request Headers 中的 Cookie
5. 粘贴到脚本提示中

---

### 方法二：手动保存

1. 在浏览器中打开文档页面
2. 右键 → 另存为 → 选择"网页，全部"
3. 保存到 `docs/erp_api/` 目录
4. 将内容复制给 AI 助手整理成 Markdown

---

## 🔌 集成计划

### 第一阶段：文档收集 ✅
- [ ] 获取 API 文档
- [ ] 整理 API 端点列表
- [ ] 记录认证方式
- [ ] 记录请求/响应格式

### 第二阶段：接口封装
- [ ] 创建 ERP API 客户端类
- [ ] 实现认证机制
- [ ] 封装常用接口（客户/订单/库存等）
- [ ] 错误处理和重试机制

### 第三阶段：业务集成
- [ ] 客户数据同步（ERP ← → Customer Hub）
- [ ] 订单状态同步
- [ ] 库存查询
- [ ] 报价单生成

### 第四阶段：自动化
- [ ] 定时同步任务
- [ ] Webhook 监听
- [ ] 数据一致性检查
- [ ] 异常告警

---

## 💻 示例代码框架

```python
# erp_integration.py

import requests
from typing import Dict, Any, List, Optional

class ZhibangERPClient:
    """智邦国际 ERP API 客户端"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.token = None
    
    def login(self) -> bool:
        """登录并获取 Token"""
        # TODO: 实现登录逻辑
        pass
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """获取客户信息"""
        # TODO: 实现接口调用
        pass
    
    def create_customer(self, customer_data: Dict) -> Optional[str]:
        """创建客户"""
        # TODO: 实现接口调用
        pass
    
    def sync_customer_to_hub(self, erp_customer_id: str) -> bool:
        """
        同步 ERP 客户到 Customer Hub
        
        流程：
        1. 从 ERP 获取客户详细信息
        2. 转换为 Customer Hub 格式
        3. 创建或更新 Contact
        4. 建档并生成 K 编码
        """
        # TODO: 实现同步逻辑
        pass
```

---

## 🔐 安全注意事项

1. **不要提交敏感信息**
   - Cookie、Token、密码等写入 `.env` 文件
   - 在 `.gitignore` 中排除 `.env`

2. **使用环境变量**
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   
   ERP_URL = os.getenv('ERP_BASE_URL')
   ERP_USERNAME = os.getenv('ERP_USERNAME')
   ERP_PASSWORD = os.getenv('ERP_PASSWORD')
   ```

3. **限制访问权限**
   - 使用只读账号抓取文档
   - 生产环境使用专用集成账号

---

## 📝 待办事项

- [ ] 完成文档抓取
- [ ] 分析 API 结构
- [ ] 设计数据映射方案（ERP ↔ Customer Hub）
- [ ] 实现认证和基础接口
- [ ] 编写集成测试用例

---

## 📞 技术支持

- **官方文档**: http://ls1.jmt.ink:46088/sysn/view/OpenApi/help.ashx
- **系统登录**: http://ls1.jmt.ink:46088/
- **技术支持**: （联系智邦国际客服）

---

**创建时间**: 2025-10-18  
**维护者**: Customer Hub Team

