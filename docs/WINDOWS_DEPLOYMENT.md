# Windows 系统部署指南

完整的Windows部署和运行指南。

---

## 🚀 一键启动（推荐）

### 方式1：使用批处理脚本（最简单）⭐⭐⭐⭐⭐

```
双击运行：quick_start.bat

系统会自动：
1. 检查Python环境
2. 创建虚拟环境
3. 安装依赖
4. 初始化数据库
5. 配置向导
6. 启动系统
```

**适合**：所有用户，尤其是不熟悉命令行的

---

### 方式2：分步安装（更可控）

#### 步骤1：安装

```
双击：setup.bat
```

完成后会：
- ✅ 创建虚拟环境
- ✅ 安装依赖
- ✅ 初始化数据库
- ✅ 添加示例知识库

#### 步骤2：配置

```
双击：config_wizard.bat
```

按提示配置：
- 大模型API Key
- 运行模式
- 白名单群聊
- 多维表格（可选）

#### 步骤3：运行

```
双击：start.bat
```

系统启动！

---

### 方式3：打包为EXE（无需Python环境）

**适合**：没有Python环境的Windows电脑

#### 在开发机上打包

```
双击：build_exe.bat
```

等待打包完成（5-10分钟）

#### 部署到目标电脑

1. 复制整个 `dist\WeChatCustomerService\` 目录
2. 在目标电脑上双击 `WeChatCustomerService.exe`
3. 完成！

---

## 📋 所有批处理脚本

| 脚本 | 用途 | 适用场景 |
|------|------|----------|
| **quick_start.bat** | 一键启动向导 | 首次使用 |
| **setup.bat** | 安装依赖 | 首次部署 |
| **config_wizard.bat** | 配置向导 | 配置API Key |
| **start.bat** | 启动系统 | 日常启动 |
| **stop.bat** | 停止系统 | 停止运行 |
| **test.bat** | 运行测试 | 健康检查 |
| **install_multimodal.bat** | 安装多模态 | 语音图片支持 |
| **build_exe.bat** | 打包exe | 无Python部署 |

---

## 🎯 三种部署方案

### 方案A：开发/测试环境

**步骤**：
```
1. 双击 setup.bat
2. 双击 config_wizard.bat
3. 设置测试模式：
   set USE_FAKE_ADAPTER=true
4. 双击 start.bat
```

**无需**：
- ❌ 真实微信
- ❌ wxauto
- ❌ Windows专机

**适合**：开发、测试、演示

---

### 方案B：生产环境（Python）

**步骤**：
```
1. 准备Windows专机
2. 安装并登录PC微信
3. 双击 setup.bat
4. 双击 config_wizard.bat
5. 配置真实模式：
   set USE_FAKE_ADAPTER=false
6. 配置大模型API Key
7. 双击 start.bat
```

**需要**：
- ✅ Windows系统
- ✅ PC微信（保持前台）
- ✅ Python 3.10+

**适合**：正式运营，有Python环境

---

### 方案C：生产环境（EXE）

**步骤**：
```
在开发机：
1. 双击 build_exe.bat（打包）
2. 复制 dist\WeChatCustomerService\ 到U盘

在生产机：
1. 复制文件夹到 C:\WeChatBot\
2. 安装并登录PC微信
3. 创建 .env 文件配置API Key
4. 双击 WeChatCustomerService.exe
```

**需要**：
- ✅ Windows系统
- ✅ PC微信
- ❌ 无需Python环境

**适合**：客户部署，无技术背景

---

## ⚙️ 环境变量配置

### 方式1：使用.env文件（推荐）

运行 `config_wizard.bat` 会自动创建 `.env` 文件

或手动创建：
```
# .env
USE_FAKE_ADAPTER=false
DEEPSEEK_API_KEY=sk-your-key-here
```

### 方式2：系统环境变量

```
Win+R → sysdm.cpl → 高级 → 环境变量

添加：
  变量名：DEEPSEEK_API_KEY
  变量值：sk-your-key-here
```

### 方式3：临时设置

```cmd
set DEEPSEEK_API_KEY=sk-your-key
set USE_FAKE_ADAPTER=false
start.bat
```

**优先级**：临时设置 > .env文件 > 系统环境变量

---

## 🔧 常用命令

### 启动系统

```cmd
:: 方式1：双击
start.bat

:: 方式2：命令行
start.bat

:: 方式3：直接运行Python
venv\Scripts\activate
python main.py
```

### 停止系统

```cmd
:: 方式1：双击
stop.bat

:: 方式2：Ctrl+C（在运行窗口）

:: 方式3：任务管理器结束Python进程
```

### 测试系统

```cmd
:: 运行所有测试
test.bat

:: 或单独测试
venv\Scripts\activate
python -m pytest tests/ -v
python ops_tools.py health
```

### 查看日志

```cmd
:: 实时查看
type logs\app.log

:: 或使用文本编辑器打开
notepad logs\app.log
```

---

## 🐛 常见问题

### Q1: 双击bat文件一闪而过

**原因**：脚本执行出错

**解决**：
```cmd
:: 在命令提示符中运行，查看错误
cmd
cd C:\path\to\project
setup.bat
```

### Q2: setup.bat 报错"找不到Python"

**原因**：Python未安装或未添加到PATH

**解决**：
```
1. 下载Python：https://www.python.org/downloads/
2. 安装时勾选"Add Python to PATH"
3. 重启命令提示符
4. 运行：python --version
```

### Q3: pip install 速度慢

**解决**：使用国内镜像（脚本已包含）

```cmd
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package_name
```

### Q4: wxauto 初始化失败

**原因**：PC微信未运行或版本不兼容

**解决**：
```
1. 确保PC微信已登录并保持前台
2. 使用最新版本PC微信
3. 以管理员权限运行
4. 或先用测试模式：set USE_FAKE_ADAPTER=true
```

### Q5: 打包exe失败

**原因**：依赖冲突或文件锁定

**解决**：
```cmd
:: 1. 清理缓存
rd /s /q build dist
del main.spec

:: 2. 重新打包
build_exe.bat
```

---

## 🔐 Windows服务化（长期运行）

### 使用NSSM（推荐）

#### 1. 下载NSSM

https://nssm.cc/download

解压到：`C:\nssm\`

#### 2. 安装服务

```cmd
:: 以管理员身份运行
cd C:\nssm\win64

:: 安装服务
nssm install WeChatBot "C:\path\to\venv\Scripts\python.exe" "C:\path\to\main.py"

:: 设置工作目录
nssm set WeChatBot AppDirectory "C:\path\to\project"

:: 设置环境变量
nssm set WeChatBot AppEnvironmentExtra "USE_FAKE_ADAPTER=false" "DEEPSEEK_API_KEY=sk-xxxxx"

:: 设置日志
nssm set WeChatBot AppStdout "C:\path\to\logs\service.log"
nssm set WeChatBot AppStderr "C:\path\to\logs\service_error.log"

:: 设置启动类型
nssm set WeChatBot Start SERVICE_AUTO_START
```

#### 3. 管理服务

```cmd
:: 启动
nssm start WeChatBot

:: 停止
nssm stop WeChatBot

:: 重启
nssm restart WeChatBot

:: 查看状态
nssm status WeChatBot

:: 卸载
nssm remove WeChatBot confirm
```

---

## 📊 性能优化

### Windows专机建议配置

**最低配置**：
- CPU：2核
- 内存：4GB
- 硬盘：20GB
- 系统：Windows 10/11

**推荐配置**：
- CPU：4核
- 内存：8GB
- 硬盘：50GB SSD
- 系统：Windows 11

### 如果安装多模态支持

**额外需求**：
- 内存：+2GB（PaddleOCR模型）
- 硬盘：+2GB（模型文件）

---

## 📝 部署检查清单

### 首次部署

- [ ] Python 3.10+ 已安装
- [ ] 运行 setup.bat
- [ ] 运行 config_wizard.bat
- [ ] 配置至少一个大模型API Key
- [ ] 运行 test.bat 检查
- [ ] 启动 start.bat

### 生产部署

- [ ] Windows专机准备
- [ ] PC微信已安装并登录
- [ ] 微信保持前台运行
- [ ] 网络连接稳定
- [ ] 配置白名单群聊
- [ ] 配置NSSM服务（可选）
- [ ] 设置开机自启动

### 多模态支持

- [ ] 运行 install_multimodal.bat
- [ ] PaddleOCR 安装成功
- [ ] FunASR 安装成功（可选）
- [ ] 测试语音识别
- [ ] 测试图片识别

---

## 🎯 快速开始

### 新手（5分钟）

```
1. 双击：quick_start.bat
2. 按提示操作
3. 完成！
```

### 有经验用户（3分钟）

```cmd
setup.bat
config_wizard.bat
start.bat
```

### 命令行用户

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -c "from storage.db import Database; db=Database('data/data.db'); db.init_database()"
set DEEPSEEK_API_KEY=sk-xxxxx
python main.py
```

---

## 📞 技术支持

**如遇问题**：
1. 查看 `logs\app.log`
2. 运行 `test.bat` 诊断
3. 查看对应文档

**文档索引**：
- 安装问题 → `INSTALLATION.md`
- 配置问题 → `START_HERE.md`
- 功能使用 → `FINAL_GUIDE.md`

---

**现在就开始：双击 `quick_start.bat`！** 🚀

**最后更新**：2025-10-16

