# 多模态支持：语音和图片处理方案

本文档介绍如何处理客户发送的语音消息和故障截图。

---

## 🎯 场景分析

### 实际客服场景

**场景1：语音消息**
```
客户发送语音："我的充电桩显示故障代码E03，是什么问题？"
```

**场景2：故障截图**
```
客户发送图片：充电桩屏幕显示"故障代码：E03 通信异常"
```

**需求**：
1. ✅ 识别语音内容（ASR）
2. ✅ 识别图片中的文字（OCR）
3. ✅ 理解故障代码
4. ✅ 从知识库检索解决方案
5. ✅ 回复客户

---

## 💡 完整技术方案

### 架构图

```
客户发送语音/图片
      ↓
微信适配器接收
      ↓
┌─────────────────────────────────┐
│  多模态处理模块                  │
│  ├── 语音 → ASR → 文字           │
│  └── 图片 → OCR → 文字           │
└──────────┬──────────────────────┘
           ↓
   文字 + 知识库检索
           ↓
      AI 生成回复
           ↓
      发送给客户
```

---

## 🎙️ 语音处理方案

### 方案A：本地ASR（推荐）⭐

**技术选型**：
- **FunASR**（阿里达摩院开源，中文最佳）
- 或 **Whisper**（OpenAI开源，多语言）

**优势**：
- ✅ 免费
- ✅ 本地部署，数据安全
- ✅ 中文识别准确率高（>95%）
- ✅ 离线可用

**示例代码**：
```python
from funasr import AutoModel

# 初始化模型（首次会下载）
asr_model = AutoModel(model="paraformer-zh")

# 识别语音
text = asr_model.generate(audio="voice.mp3")
print(text)  # "我的充电桩显示故障代码E03是什么问题"
```

**成本**：免费（本地部署）

---

### 方案B：云端ASR

**技术选型**：
- 百度语音识别（中文准确率高）
- 腾讯云ASR
- 阿里云ASR

**优势**：
- ✅ 无需部署
- ✅ API调用简单
- ✅ 准确率高

**劣势**：
- ❌ 需要付费
- ❌ 数据上云

**示例代码**：
```python
import requests

def baidu_asr(audio_file: str, api_key: str) -> str:
    """百度语音识别"""
    # 获取access_token
    token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret}"
    token = requests.get(token_url).json()['access_token']
    
    # 识别语音
    with open(audio_file, 'rb') as f:
        audio_data = f.read()
    
    url = f"https://vop.baidu.com/server_api?dev_pid=1537&cuid=python&token={token}"
    headers = {'Content-Type': 'audio/pcm;rate=16000'}
    
    response = requests.post(url, headers=headers, data=audio_data)
    result = response.json()
    
    return result['result'][0]  # 识别结果
```

**成本**：约 ¥0.016/次（百度）

---

## 🖼️ 图片处理方案

### 方案A：OCR + 视觉理解（推荐）⭐

**两步处理**：

#### 第一步：OCR提取文字

**PaddleOCR**（已集成）：
```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='ch')
result = ocr.ocr('fault_screen.jpg', cls=True)

# 提取所有文字
texts = []
for line in result[0]:
    texts.append(line[1][0])

text = '\n'.join(texts)
print(text)
# 输出：
# 故障代码：E03
# 通信异常
# 请联系售后
```

**优势**：
- ✅ 免费
- ✅ 中文准确率高（>98%）
- ✅ 已集成在知识库模块

#### 第二步：视觉理解（高级）

**使用支持视觉的大模型**：
- GPT-4V（OpenAI）
- Claude 3（Anthropic）
- Gemini Pro Vision（Google）
- 通义千问 VL（阿里）

**示例**：
```python
import base64

# 读取图片
with open('fault_screen.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

# 调用GPT-4V
response = openai.chat.completions.create(
    model="gpt-4o",  # 支持视觉
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "这是充电桩的故障截图，请分析故障原因"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
# 输出：
# 根据截图显示，充电桩出现E03故障代码，这通常表示通信异常。
# 可能原因：① 网络连接断开 ② CAN总线故障 ③ 控制板通信中断
# 建议：先检查网络连接...
```

**优势**：
- ✅ 直接理解图片内容
- ✅ 无需OCR
- ✅ 可以识别仪表盘、指示灯状态等

**成本**：
- GPT-4V：约 $0.01/图片
- Claude 3：约 $0.003/图片

---

### 方案B：纯OCR（成本低）

只使用PaddleOCR提取文字，然后用普通LLM处理：

```python
# 1. OCR识别
text = ocr_extract('fault_screen.jpg')
# 结果："故障代码：E03 通信异常"

# 2. 添加上下文后查询
query = f"客户发来故障截图，显示：{text}"

# 3. 知识库检索
evidences = retriever.retrieve(query)

# 4. AI生成回复（使用普通模型，更便宜）
response = ai_gateway.generate(
    user_message=query,
    evidence_context=evidences
)
```

**优势**：
- ✅ 成本极低（OCR免费）
- ✅ 效果已经很好（90%场景）

**劣势**：
- ❌ 无法识别非文字信息（指示灯、仪表等）

---

## 🛠️ 技术实现

让我为您实现完整的多模态支持！

### 模块结构

```
multimodal/
├── __init__.py
├── audio_handler.py     # 语音处理
├── image_handler.py     # 图片处理
└── vision_models.py     # 视觉大模型
```

---

## 📊 方案对比

### 语音处理

| 方案 | 成本 | 准确率 | 延迟 | 推荐度 |
|------|------|--------|------|--------|
| **FunASR（本地）** | 免费 | 95% | 1-2s | ⭐⭐⭐⭐⭐ |
| Whisper（本地） | 免费 | 97% | 2-3s | ⭐⭐⭐⭐ |
| 百度ASR（云端） | ¥0.016/次 | 98% | 0.5s | ⭐⭐⭐⭐ |
| 微信内置转文字 | 免费 | 90% | 即时 | ⭐⭐⭐ |

### 图片处理

| 方案 | 成本 | 准确率 | 功能 | 推荐度 |
|------|------|--------|------|--------|
| **PaddleOCR + LLM** | 免费 | 90% | 文字识别 | ⭐⭐⭐⭐⭐ |
| GPT-4V | $0.01/张 | 98% | 完整理解 | ⭐⭐⭐⭐ |
| Claude 3 Vision | $0.003/张 | 97% | 完整理解 | ⭐⭐⭐⭐ |
| Gemini Pro Vision | 免费额度 | 95% | 完整理解 | ⭐⭐⭐⭐ |

---

## 🎯 我的推荐

### 推荐方案：PaddleOCR + FunASR + 普通LLM ⭐⭐⭐⭐⭐

**技术栈**：
- 语音识别：FunASR（本地，免费）
- 图片识别：PaddleOCR（本地，免费）
- 文字理解：DeepSeek/GPT-4o-mini（便宜）

**优势**：
- ✅ 成本极低（只付LLM费用）
- ✅ 准确率足够（90%+）
- ✅ 数据安全（本地处理）
- ✅ 响应快速（1-3秒）

**适用场景**：
- 90%的客服场景（文字为主的故障截图）
- 如：充电桩故障代码、错误信息、参数显示等

### 高级方案：视觉大模型（可选）

**使用场景**：
- 需要识别非文字信息（指示灯、仪表读数、接线图等）
- 复杂的故障现场照片
- 需要理解图片上下文

**推荐**：
- **Gemini Pro Vision**（有免费额度）
- 或 **GPT-4V**（效果最好）

---

## 💰 成本对比

### 方案A：纯本地处理（推荐）

**每月成本**（1000次语音 + 1000张图片）：
```
FunASR：免费
PaddleOCR：免费
DeepSeek LLM：¥100/月
────────────────
总计：¥100/月
```

### 方案B：混合方案

**每月成本**（1000次语音 + 1000张图片）：
```
FunASR：免费
PaddleOCR：免费
GPT-4V（10%图片）：$1（¥7）
GPT-4o-mini LLM：¥300/月
────────────────
总计：¥307/月
```

### 方案C：纯云端

**每月成本**（1000次语音 + 1000张图片）：
```
百度ASR：¥16
百度OCR：¥50
OpenAI LLM：¥500/月
────────────────
总计：¥566/月
```

**结论：方案A（纯本地）性价比最高！**

---

## ⚠️ 企业微信的额外限制

### 在企业微信中处理语音/图片

**需要额外步骤**：

```python
# 1. 接收消息（只有media_id）
message = {
    "MsgType": "voice",
    "MediaId": "MEDIA_ID_12345"
}

# 2. 下载文件（额外API调用）
import requests

url = f"https://qyapi.weixin.qq.com/cgi-bin/media/get"
params = {
    "access_token": access_token,
    "media_id": "MEDIA_ID_12345"
}

response = requests.get(url, params=params)

# 3. 保存到本地
with open('temp_voice.amr', 'wb') as f:
    f.write(response.content)

# 4. 转换格式（企业微信语音是AMR格式）
import subprocess
subprocess.run(['ffmpeg', '-i', 'temp_voice.amr', 'temp_voice.wav'])

# 5. ASR识别
text = asr_model.generate('temp_voice.wav')

# 6. 清理临时文件
os.remove('temp_voice.amr')
os.remove('temp_voice.wav')
```

**复杂度**：+100行代码  
**延迟**：+1-2秒（下载+转换）

---

## 🎯 对于你的场景

### 你的需求

> 客户会发送语音信息或充电桩故障屏幕的截图

### 我的建议

**继续使用个人微信（wxauto）+ 多模态处理**

**理由**：
1. ✅ **处理更简单**：直接获取语音/图片文件
2. ✅ **客户体验好**：无需改变使用习惯
3. ✅ **功能完整**：无API限制
4. ✅ **成本更低**：少一个下载步骤

**风险控制**：
- 已实现拟人化行为
- 严格频率限制
- 小规模试点（1-3个群）
- 准备企业微信B计划

---

## 🚀 实施建议

### 立即实施（个人微信方案）

**我将为你实现**：

1. **语音处理模块**
   - FunASR集成（中文最佳）
   - 自动转文字
   - 缓存优化

2. **图片处理模块**
   - PaddleOCR提取文字
   - 故障代码识别
   - 可选：GPT-4V理解

3. **微信适配器增强**
   - 支持接收语音消息
   - 支持接收图片消息
   - 自动调用多模态处理

4. **知识库增强**
   - 故障代码库
   - 图片知识库

### 使用流程

```
客户：[语音] "充电桩E03故障"
  ↓ ASR识别
系统："客户说：充电桩E03故障"
  ↓ 知识库检索
AI："E03是通信异常，请检查：① 网络连接 ② ..."
  ↓ 发送
客户：收到回复

客户：[图片] 充电桩屏幕截图
  ↓ OCR识别
系统："图片显示：故障代码E03 通信异常"
  ↓ 知识库检索
AI："根据故障代码，这是通信问题..."
  ↓ 发送
客户：收到回复
```

---

## 📊 总结对比表

| 功能 | 个人微信 | 企业微信 |
|------|---------|---------|
| **接收语音** | ✅ 直接获取文件 | ⚠️ 需下载（media_id） |
| **接收图片** | ✅ 直接获取文件 | ⚠️ 需下载（media_id） |
| **处理复杂度** | 简单 | 复杂（+100行代码） |
| **响应延迟** | 1-2秒 | 2-4秒（多一次下载） |
| **封号风险** | 有（可控） | 无 |
| **客户门槛** | 低 | 高（需加入企业微信） |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🎯 最终建议

**对于你的充电桩客服场景**：

**推荐：个人微信（wxauto）+ 完整多模态支持**

**原因**：
1. ✅ 语音和图片处理更简单直接
2. ✅ 客户无需改变习惯
3. ✅ 充电桩故障图主要是文字（OCR足够）
4. ✅ 已有完整防封机制

**实施计划**：
```
第1步：实现多模态处理（我现在帮你做）
第2步：部署测试（1-2个群）
第3步：观察运行（2-4周）
第4步：根据效果决定是否需要企业微信
```

**下一步**：我立即为你实现完整的语音和图片处理功能！

