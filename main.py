#!/usr/bin/env python3
"""
Wxauto 智能客服中台 - 统一启动入口 v2.0
重构后的架构：C/S分离，统一使用 server 端处理
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """统一启动入口"""
    parser = argparse.ArgumentParser(description='Wxauto 智能客服中台')
    parser.add_argument(
        'mode',
        choices=['server', 'client', 'web', 'legacy'],
        help='启动模式：server(服务端) | client(客户端) | web(管理后台) | legacy(旧版单体)'
    )
    parser.add_argument('--host', default='0.0.0.0', help='服务器地址（仅server模式）')
    parser.add_argument('--port', type=int, default=8000, help='服务器端口（仅server模式）')
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    if args.mode == 'server':
        print("🚀 启动服务端...")
        from server.main_server import main as server_main
        server_main()
    
    elif args.mode == 'client':
        print("📱 启动客户端...")
        from client.main_client import main as client_main
        client_main()
    
    elif args.mode == 'web':
        print("🌐 启动Web管理后台...")
        from web.web_frontend import main as web_main
        web_main()
    
    elif args.mode == 'legacy':
        print("⚠️  使用旧版单体模式（已废弃，仅用于兼容测试）")
        print("💡 建议：使用 'python main.py server' + 'python main.py client' 替代")
        from legacy_main import CustomerServiceBot
        bot = CustomerServiceBot(config_path=args.config, use_fake=True)
        bot.run()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 程序已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

