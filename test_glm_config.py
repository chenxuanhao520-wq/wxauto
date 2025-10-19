#!/usr/bin/env python3
"""
测试智谱 GLM API 配置
"""
import os
import requests
import json

# GLM 配置
API_KEY = os.getenv("GLM_API_KEY", "your-glm-api-key-here")
BASE_URL = "https://open.bigmodel.cn/api/coding/paas/v4"

def test_glm_connection():
    """测试 GLM API 连接"""
    
    print("=" * 60)
    print("🧪 测试智谱 GLM API 配置")
    print("=" * 60)
    
    # 测试 1: 检查接口地址
    print(f"\n📍 接口地址: {BASE_URL}")
    
    # 测试 2: 尝试调用 chat completions
    url = f"{BASE_URL}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "glm-4-flash",  # 使用最快的模型测试
        "messages": [
            {
                "role": "user",
                "content": "你好，这是一个连接测试"
            }
        ],
        "max_tokens": 10
    }
    
    print(f"\n🔑 API Key: {API_KEY[:20]}...{API_KEY[-10:]}")
    print(f"📦 测试模型: glm-4-flash")
    print(f"\n⏳ 正在发送请求...")
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"\n📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 连接成功！")
            result = response.json()
            print(f"\n📝 API 响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0].get('message', {}).get('content', '')
                print(f"\n💬 模型回复: {content}")
            
            return True
        else:
            print(f"❌ 连接失败！")
            print(f"\n错误详情:")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时！请检查网络连接")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器！请检查接口地址")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False

def test_available_models():
    """测试可用的模型列表"""
    print("\n" + "=" * 60)
    print("📋 智谱 GLM 常用模型")
    print("=" * 60)
    
    models = [
        ("glm-4-flash", "最快，适合简单对话", "免费"),
        ("glm-4", "标准模型，性能均衡", "0.1元/千tokens"),
        ("glm-4-plus", "增强版，更强推理", "0.5元/千tokens"),
        ("glm-4-air", "轻量级，速度快", "0.001元/千tokens"),
    ]
    
    for model_name, desc, price in models:
        print(f"\n• {model_name:20} - {desc:30} [{price}]")

if __name__ == "__main__":
    # 测试连接
    success = test_glm_connection()
    
    # 显示可用模型
    test_available_models()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ GLM 配置正确，可以正常使用！")
    else:
        print("❌ GLM 配置有问题，请检查：")
        print("   1. API Key 是否正确")
        print("   2. 接口地址是否正确")
        print("   3. 网络连接是否正常")
        print("   4. 账户余额是否充足")
    print("=" * 60)

