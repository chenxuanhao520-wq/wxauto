# 📘 wxauto 完整对接说明

**参考项目**: https://github.com/cluic/wxauto  
**官方文档**: https://docs.wxauto.org  
**Plus版本**: https://docs.wxauto.org/plus.html

---

## 🔍 两个版本说明

### 1. 开源版 (wxauto)

- **GitHub**: https://github.com/cluic/wxauto
- **包名**: `wxauto`
- **费用**: 免费
- **安装**: `pip install wxauto`
- **导入**: `from wxauto import WeChat`

### 2. Plus版 (wxautox)

- **官网**: https://plus.wxauto.org
- **包名**: `wxautox`
- **费用**: 需要激活码（付费）
- **安装**: `pip install wxautox`
- **导入**: `from wxautox4 import WeChat`
- **激活**: `wxautox -a [激活码]`

---

## 🎯 项目对接状态

### ✅ 已完成的对接

1. **自动版本检测**
   - 优先尝试 Plus 版 (wxautox4)
   - 不可用时自动降级到开源版

2. **代码位置**
   - 文件: `modules/adapters/wxauto_adapter.py`
   - 方法: `_init_wxauto()`

3. **配置管理**
   - 配置项: `use_plus` (默认 False)
   - 配置文件: `client/config/client_config.yaml`

### 📝 使用方式

```python
# 方式1: 使用开源版（默认）
from modules.adapters.wxauto_adapter import WxAutoAdapter

adapter = WxAutoAdapter(whitelisted_groups=["群1", "群2"])

# 方式2: 优先使用Plus版
adapter = WxAutoAdapter(
    whitelisted_groups=["群1", "群2"],
    use_plus=True  # 启用Plus版
)
```

### ⚙️ 配置文件

```yaml
# client/config/client_config.yaml
wechat:
  use_plus: false  # 设置为 true 需要先安装并激活 wxautox
  whitelisted_groups:
    - "充电桩技术支持群"
```

---

## 🔧 Plus版功能优势

根据官方文档，Plus版相比开源版：

1. **消息功能增强**
   - ✅ 发送自定义表情包
   - ✅ @所有人
   - ✅ 获取好友列表
   - ✅ 发送好友请求

2. **性能优化**
   - Bug修复
   - 更高效的性能
   - 后台模式支持

3. **专属支持**
   - Plus群专属技术支持
   - 优先获得更新

---

## 📋 项目已经支持的API

### 基于开源版优化

```python
# 1. 消息监听（已优化）
wx.AddListenChat(nickname="群名", callback=handler)

# 2. 消息发送（已优化）
wx.SendMsg(text, who="群名")

# 3. 获取消息
wx.GetAllMessage()

# 4. 移除监听
wx.RemoveListenChat(nickname="群名")
```

### Plus版额外功能

```python
# 如果使用了Plus版，可以使用额外功能：
# (具体API以官方文档为准)

# 1. 发送自定义表情包
wx.SendCustomEmoji(...)

# 2. @所有人
wx.AtAll(...)

# 3. 获取好友列表
friends = wx.GetFriends()

# 4. 后台模式
wx.EnableBackgroundMode(True)
```

---

## 🚀 部署建议

### 开发/测试环境

- 使用开源版 (wxauto)
- 免费、稳定
- 满足基本需求

### 生产环境

- 考虑使用 Plus 版 (wxautox)
- 性能更好
- 功能更多
- 需要付费激活

---

## ⚠️ 重要提示

1. **Plus版需要付费**
   - 访问 https://docs.wxauto.org/plus.html
   - 购买激活码
   - 运行 `wxautox -a [激活码]` 激活

2. **导入包名不同**
   - 开源版: `from wxauto import WeChat`
   - Plus版: `from wxautox4 import WeChat`

3. **向后兼容**
   - 项目已支持两种版本
   - 自动检测并降级
   - 配置灵活

---

## 📚 参考资源

1. **GitHub仓库**: https://github.com/cluic/wxauto
2. **官方文档**: https://docs.wxauto.org
3. **Plus版文档**: https://docs.wxauto.org/plus.html
4. **项目代码**: `modules/adapters/wxauto_adapter.py`

---

**最后更新**: 2025-10-26  
**状态**: ✅ 已对接，支持双版本
