# 📋 wxautox (Plus版本) 对接方案更正

**重要**: 之前理解有误，已更正！

---

## 🔍 真相澄清

### wxauto Plus 的实际情况

根据官方文档 https://docs.wxauto.org/plus.html：

1. **Plus版本名称**: `wxautox` (不是 `wxauto-plus`)
2. **安装方式**: 
   ```bash
   pip install wxautox
   ```
3. **激活方式**: 
   ```bash
   wxautox -a [激活码]  # 需要购买激活码
   ```
4. **导入方式**:
   ```python
   # 开源版
   from wxauto import WeChat
   
   # Plus版
   from wxautox4 import WeChat  # 注意：从 wxautox4 导入
   ```

---

## 📊 Plus版 vs 开源版对比

### 关键差异

| 项目 | 开源版 (wxauto) | Plus版 (wxautox) |
|------|----------------|------------------|
| **包名** | `wxauto` | `wxautox` |
| **导入** | `from wxauto import WeChat` | `from wxautox4 import WeChat` |
| **费用** | 免费 | 需要激活码(付费) |
| **安装** | `pip install wxauto` | `pip install wxautox` |
| **激活** | 不需要 | `wxautox -a [激活码]` |

### Plus版新增功能

1. **发送自定义表情包** - 开源版不支持
2. **@所有人** - 开源版不支持
3. **获取好友列表** - 开源版不支持
4. **发送好友请求** - 开源版不支持
5. **后台模式** - 可能不需要最小化微信窗口
6. **Bug修复和性能优化**

---

## 🔧 正确的对接方案

### 方案1: 优先使用Plus版（如果已购买）

```python
# modules/adapters/wxauto_adapter.py

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class WxAutoAdapter:
    def __init__(self, whitelisted_groups: list, use_plus: bool = False):
        self.wx = None
        self.is_plus = False
        
        try:
            # 优先尝试Plus版
            if use_plus:
                try:
                    from wxautox4 import WeChat  # Plus版
                    self.wx = WeChat()
                    self.is_plus = True
                    logger.info("✅ 使用 wxautox4 (Plus版)")
                except ImportError:
                    logger.warning("Plus版未安装，降级到开源版")
                    from wxauto import WeChat
                    self.wx = WeChat()
                    logger.info("✅ 使用 wxauto (开源版)")
            else:
                # 使用开源版
                from wxauto import WeChat
                self.wx = WeChat()
                logger.info("✅ 使用 wxauto (开源版)")
                
        except ImportError as e:
            logger.error(f"❌ wxauto未安装: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            raise
```

### 方案2: 自动检测版本

```python
def _init_wxauto(self):
    """自动检测并使用可用版本"""
    try:
        # 1. 优先尝试Plus版
        try:
            from wxautox4 import WeChat
            self.wx = WeChat()
            self.is_plus = True
            logger.info("✅ wxautox4 (Plus版) 初始化成功")
            return
        except ImportError:
            pass
        
        # 2. 降级到开源版
        from wxauto import WeChat
        self.wx = WeChat()
        self.is_plus = False
        logger.info("✅ wxauto (开源版) 初始化成功")
        
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        raise
```

---

## ⚙️ 配置管理

### 客户端配置 (`client/config/client_config.yaml`)

```yaml
wechat:
  # 是否使用Plus版
  use_plus: false  # 设置为 true 需要先安装并激活 wxautox
  
  # 白名单群聊
  whitelisted_groups:
    - "充电桩技术支持群"
    - "VIP客户服务群"
```

---

## 🚨 重要注意事项

1. **Plus版需要付费激活**
   - 需要购买激活码
   - 运行 `wxautox -a [激活码]` 激活

2. **导入包名不同**
   - 开源版: `from wxauto import WeChat`
   - Plus版: `from wxautox4 import WeChat`

3. **向后兼容**
   - 代码需要同时支持两种导入方式
   - 优先使用Plus版，不可用时自动降级

4. **购买信息**
   - 访问: https://docs.wxauto.org/plus.html
   - 需要通过官方渠道购买激活码

---

## 📝 更新代码

需要修改 `modules/adapters/wxauto_adapter.py`:

1. 添加自动检测逻辑
2. 支持从 `wxautox4` 导入
3. 保持向后兼容
4. 记录使用的版本

---

## 🎯 实施步骤

1. ✅ 了解Plus版真实情况
2. ⏳ 修改适配器代码
3. ⏳ 添加配置选项
4. ⏳ 测试两种版本
5. ⏳ 更新文档

---

**最后更新**: 2025-10-26  
**状态**: 已更正理解，准备对接
