#!/usr/bin/env python3
"""
Cursor GLM 配置问题诊断和修复工具
"""
import os
import requests
import json

def test_glm_endpoints():
    """测试不同的 GLM API 端点"""
    
    api_key = os.getenv("GLM_API_KEY", "your-glm-api-key-here")
    
    # 可能的端点
    endpoints = [
        ("https://open.bigmodel.cn/api/paas/v4", "标准端点"),
        ("https://open.bigmodel.cn/api/coding/paas/v4", "Coding端点"),
        ("https://api.chatglm.com/v3", "旧版端点"),
    ]
    
    # 可能的模型名称
    models = [
        "glm-4-flash",
        "glm-4",
        "glm-4-air",
        "glm-4-plus",
        "chatglm3",
        "chatglm_pro",
    ]
    
    print("=" * 80)
    print("🔍 GLM API 端点和模型测试")
    print("=" * 80)
    
    working_configs = []
    
    for endpoint, desc in endpoints:
        print(f"\n📍 测试端点: {endpoint} ({desc})")
        
        for model in models:
            url = f"{endpoint}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "测试"
                    }
                ],
                "max_tokens": 5
            }
            
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"  ✅ {model}: 成功")
                    working_configs.append({
                        "endpoint": endpoint,
                        "model": model,
                        "description": desc
                    })
                elif response.status_code == 400:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "")
                    if "模型不存在" in error_msg:
                        print(f"  ❌ {model}: 模型不存在")
                    else:
                        print(f"  ❌ {model}: {error_msg}")
                elif response.status_code == 401:
                    print(f"  🔑 {model}: API Key 无效")
                    break  # API Key 无效，无需测试其他模型
                else:
                    print(f"  ❌ {model}: HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"  ⏱️ {model}: 超时")
            except requests.exceptions.ConnectionError:
                print(f"  🌐 {model}: 连接失败")
                break  # 端点不可达，无需测试其他模型
            except Exception as e:
                print(f"  ❌ {model}: {str(e)}")
    
    print("\n" + "=" * 80)
    print("📋 可用的配置组合")
    print("=" * 80)
    
    if working_configs:
        for i, config in enumerate(working_configs, 1):
            print(f"\n{i}. {config['description']}")
            print(f"   端点: {config['endpoint']}")
            print(f"   模型: {config['model']}")
    else:
        print("\n❌ 没有找到可用的配置组合")
        print("\n可能的原因:")
        print("1. API Key 无效或已过期")
        print("2. 账户余额不足")
        print("3. 网络连接问题")
        print("4. 智谱AI服务暂时不可用")
    
    return working_configs

def generate_cursor_config():
    """生成 Cursor 配置指南"""
    
    print("\n" + "=" * 80)
    print("🛠️ Cursor 配置指南")
    print("=" * 80)
    
    print("\n📝 方法 1: 使用 OpenAI 兼容模式（推荐）")
    print("-" * 50)
    print("1. 打开 Cursor 设置 (Cmd + ,)")
    print("2. 搜索 'OpenAI'")
    print("3. 填写以下配置:")
    print("   • OpenAI API Key: 2853e43adea74724865746c7ddfcd7ad.qp589y9s3P2KRlI4")
    print("   • Override OpenAI Base URL: https://open.bigmodel.cn/api/paas/v4")
    print("   • Model: glm-4-flash")
    print("4. 保存设置并重启 Cursor")
    
    print("\n📝 方法 2: 使用自定义模型")
    print("-" * 50)
    print("1. 打开 Cursor 设置")
    print("2. 找到 'Models' 或 'AI Providers'")
    print("3. 点击 'Add Custom Model'")
    print("4. 填写以下配置:")
    print("   • Provider: OpenAI Compatible")
    print("   • Model Name: glm-4-flash")
    print("   • Display Name: 智谱 GLM-4-Flash")
    print("   • API Key: 2853e43adea74724865746c7ddfcd7ad.qp589y9s3P2KRlI4")
    print("   • Base URL: https://open.bigmodel.cn/api/paas/v4")
    print("5. 保存并选择该模型")
    
    print("\n⚠️ 常见错误和解决方案")
    print("-" * 50)
    print("❌ 错误: '模型不存在，请检查模型代码'")
    print("   解决: 使用 'glm-4-flash' 而不是其他变体")
    print("\n❌ 错误: 'Unauthorized User API key'")
    print("   解决: 确保 API Key 填写在正确的字段，无多余空格")
    print("\n❌ 错误: 'Unable to reach the model provider'")
    print("   解决: 检查 Base URL，确保是 'https://open.bigmodel.cn/api/paas/v4'")
    
    print("\n🧪 验证配置")
    print("-" * 50)
    print("1. 打开 Cursor Chat (Cmd + L)")
    print("2. 选择 GLM 模型")
    print("3. 发送测试消息: '你好'")
    print("4. 如果收到回复，配置成功！")

if __name__ == "__main__":
    # 测试 API
    working_configs = test_glm_endpoints()
    
    # 生成配置指南
    generate_cursor_config()
    
    print("\n" + "=" * 80)
    print("🎯 总结")
    print("=" * 80)
    
    if working_configs:
        print("✅ 找到可用的配置！请按照上面的指南配置 Cursor")
    else:
        print("❌ API 测试失败，请检查:")
        print("   1. API Key 是否正确")
        print("   2. 账户余额是否充足")
        print("   3. 网络连接是否正常")
        print("   4. 智谱AI服务是否可用")
    
    print("\n如果问题仍然存在，请提供:")
    print("• Cursor 设置页面的截图")
    print("• 具体的错误信息")
    print("• 您使用的 Cursor 版本")
