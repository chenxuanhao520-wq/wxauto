# Windows 用户必读

专为Windows用户准备的一页纸快速指南。

---

## 🚀 最简单的开始方式

### 双击这个文件：`quick_start.bat` ⭐⭐⭐⭐⭐

**它会自动完成**：
1. ✅ 检查Python环境
2. ✅ 创建虚拟环境  
3. ✅ 安装所有依赖
4. ✅ 初始化数据库
5. ✅ 引导您配置API Key
6. ✅ 启动系统

**所需时间**：5-10分钟（首次运行）

**就这么简单！** 🎉

---

## 📁 所有批处理脚本说明

### 日常使用

| 文件 | 用途 | 何时使用 |
|------|------|----------|
| **quick_start.bat** | 🚀 一键启动向导 | 首次使用 |
| **start.bat** | ▶️ 启动系统 | 每次启动 |
| **stop.bat** | ⏹️ 停止系统 | 停止运行 |
| **test.bat** | 🧪 运行测试 | 检查健康状态 |

### 安装配置

| 文件 | 用途 | 何时使用 |
|------|------|----------|
| **setup.bat** | 📦 安装依赖 | 首次部署 |
| **config_wizard.bat** | ⚙️ 配置向导 | 配置API Key |
| **install_multimodal.bat** | 🎙️ 安装语音图片支持 | 可选功能 |

### 高级功能

| 文件 | 用途 | 何时使用 |
|------|------|----------|
| **build_exe.bat** | 📦 打包exe | 部署到其他电脑 |

---

## 🎯 三种使用方式

### 方式1：测试模式（不需要真实微信）

```
1. 双击：quick_start.bat
2. 选择：DeepSeek（最便宜）
3. 输入API Key
4. 完成！

系统会模拟微信消息，用于测试
```

**适合**：学习、测试、演示

---

### 方式2：真实模式（连接PC微信）

```
1. 打开并登录PC微信（保持前台）
2. 双击：quick_start.bat
3. 配置API Key
4. 在配置文件中设置：
   USE_FAKE_ADAPTER=false
5. 运行

系统会自动监听微信群消息
```

**适合**：正式运营

---

### 方式3：打包exe（部署到其他电脑）

```
在您的电脑（开发机）：
1. 双击：build_exe.bat
2. 等待打包完成（10分钟）
3. 复制 dist\WeChatCustomerService\ 到U盘

在客户电脑（生产机）：
1. 复制文件夹到 C:\WeChatBot\
2. 打开并登录PC微信
3. 创建 .env 文件，配置API Key
4. 双击 WeChatCustomerService.exe

无需安装Python！
```

**适合**：客户部署、多台电脑

---

## ⚙️ 配置API Key

### 最简单方式：运行配置向导

```
双击：config_wizard.bat
```

按提示输入API Key，自动创建`.env`文件

---

### 手动配置

创建文件：`.env`

```
USE_FAKE_ADAPTER=false
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
```

保存后运行 `start.bat`

---

## 🎙️ 添加语音和图片识别（可选）

### 如果需要处理客户的语音和故障截图

```
双击：install_multimodal.bat
```

会安装：
- PaddleOCR（图片文字识别）
- FunASR（语音识别，可选）

**安装后，系统自动支持**：
- 客户发送语音 → 自动转文字 → AI回复
- 客户发送图片 → 识别故障代码 → AI回复

---

## 📊 常见场景

### 场景1：每天启动系统

```
1. 打开并登录PC微信
2. 双击：start.bat
3. 系统开始监听群消息
4. 工作结束后，双击：stop.bat
```

### 场景2：健康检查

```
双击：test.bat

会显示：
✅ 数据库正常
✅ AI 网关可用
✅ 知识库已加载
```

### 场景3：查看运行日志

```
打开文件：logs\app.log
```

### 场景4：上传新的故障手册

```cmd
:: 在命令提示符中
venv\Scripts\activate
python upload_documents.py upload --file 故障手册.pdf
```

---

## 🐛 遇到问题？

### 运行test.bat检查

```
双击：test.bat

查看哪里有问题：
- 数据库？
- API Key？
- 知识库？
```

### 查看日志

```
logs\app.log  - 运行日志
```

### 查看文档

```
START_HERE.md - 快速开始
FINAL_GUIDE.md - 完整指南
docs\WINDOWS_DEPLOYMENT.md - Windows部署
```

---

## 💡 推荐工作流程

### 第一次使用

```
1. 双击：quick_start.bat
2. 按提示完成配置
3. 系统自动启动
4. 在微信群测试 @机器人
```

### 日常使用

```
每天：
  上午：双击 start.bat
  下午：双击 stop.bat
```

### 每周维护

```
周日：双击 test.bat（健康检查）
```

---

## 📁 文件位置

```
C:\WeChatBot\                   # 项目目录
│
├── quick_start.bat             # ⭐ 一键启动（首次用这个）
├── start.bat                   # ▶️ 启动系统（日常用这个）
├── stop.bat                    # ⏹️ 停止系统
├── test.bat                    # 🧪 测试检查
│
├── setup.bat                   # 安装脚本
├── config_wizard.bat           # 配置向导
├── install_multimodal.bat      # 安装语音图片支持
├── build_exe.bat               # 打包exe
│
├── venv\                       # 虚拟环境（自动创建）
├── data\                       # 数据目录（自动创建）
│   └── data.db                 # 数据库
├── logs\                       # 日志目录（自动创建）
│   └── app.log                 # 运行日志
│
├── .env                        # 配置文件（自动创建）
├── config.yaml                 # 系统配置
│
├── START_HERE.md               # 📖 快速开始
├── FINAL_GUIDE.md              # 📖 完整指南
└── docs\                       # 📖 所有文档
```

---

## 🎊 准备好了吗？

### 立即开始

```
在Windows电脑上：

1. 双击：quick_start.bat
2. 等待安装完成
3. 输入DeepSeek API Key
4. 开始使用！
```

**3-5分钟后，您就有了一个能用的AI客服系统！**

---

## 📞 需要帮助？

**Windows部署问题**：
- 查看：`docs\WINDOWS_DEPLOYMENT.md`

**功能使用问题**：
- 查看：`FINAL_GUIDE.md`

**语音图片处理**：
- 查看：`docs\MULTIMODAL_SUPPORT.md`

**充电桩场景**：
- 查看：`docs\CHARGING_PILE_SOLUTION.md`

---

**双击 `quick_start.bat` 开始吧！** 🚀

**版本**：v3.1  
**更新**：2025-10-16

