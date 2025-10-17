#!/usr/bin/env python3
"""
多维表格同步工具
支持将消息日志同步到飞书/钉钉多维表格
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from integrations import FeishuBitable, DingtalkBitable


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def sync_to_feishu(db_path: str, days: int = 7, sync_type: str = 'messages'):
    """同步到飞书多维表格"""
    if sync_type == 'conversations':
        print_header("同步对话到飞书多维表格")
    else:
        print_header("同步消息到飞书多维表格")
    
    feishu = FeishuBitable()
    
    if not feishu.is_configured():
        print("❌ 飞书多维表格未配置")
        print("\n请设置以下环境变量：")
        print("  FEISHU_APP_ID=your_app_id")
        print("  FEISHU_APP_SECRET=your_app_secret")
        print("  FEISHU_BITABLE_TOKEN=your_bitable_token")
        print("  FEISHU_TABLE_ID=your_table_id")
        return False
    
    print(f"配置检查：")
    print(f"  App ID: {feishu.app_id[:8]}...")
    print(f"  Bitable Token: {feishu.bitable_token[:8]}...")
    print(f"  Table ID: {feishu.table_id}")
    
    # 同步最近 N 天的数据
    since = datetime.now() - timedelta(days=days)
    print(f"\n同步范围：{since.strftime('%Y-%m-%d %H:%M:%S')} 至今")
    print(f"同步类型：{sync_type}")
    
    if sync_type == 'conversations':
        count = feishu.sync_conversations_from_database(db_path, since=since)
        item_name = "对话"
    else:
        count = feishu.sync_from_database(db_path, since=since)
        item_name = "消息"
    
    if count > 0:
        print(f"\n✅ 同步成功：{count} 条{item_name}")
        return True
    else:
        print(f"\n⚠️  同步完成：0 条{item_name}")
        return False


def sync_to_dingtalk(db_path: str, days: int = 7):
    """同步到钉钉多维表格"""
    print_header("同步到钉钉多维表格")
    
    dingtalk = DingtalkBitable()
    
    if not dingtalk.is_configured():
        print("❌ 钉钉多维表格未配置")
        print("\n请设置以下环境变量：")
        print("  DINGTALK_APP_KEY=your_app_key")
        print("  DINGTALK_APP_SECRET=your_app_secret")
        print("  DINGTALK_BASE_ID=your_base_id")
        print("  DINGTALK_TABLE_ID=your_table_id")
        return False
    
    print(f"配置检查：")
    print(f"  App Key: {dingtalk.app_key[:8]}...")
    print(f"  Base ID: {dingtalk.base_id}")
    print(f"  Table ID: {dingtalk.table_id}")
    
    # 同步最近 N 天的数据
    since = datetime.now() - timedelta(days=days)
    print(f"\n同步范围：{since.strftime('%Y-%m-%d %H:%M:%S')} 至今")
    
    count = dingtalk.sync_from_database(db_path, since=since)
    
    if count > 0:
        print(f"\n✅ 同步成功：{count} 条记录")
        return True
    else:
        print(f"\n⚠️  同步完成：0 条记录")
        return False


def test_feishu_connection():
    """测试飞书连接"""
    print_header("测试飞书连接")
    
    feishu = FeishuBitable()
    
    if not feishu.is_configured():
        print("❌ 飞书多维表格未配置")
        return False
    
    # 尝试获取 access_token
    token = feishu._get_access_token()
    
    if token:
        print(f"✅ Access Token 获取成功")
        print(f"   Token: {token[:20]}...")
        
        # 尝试写入一条测试记录
        test_record = {
            'request_id': 'test_' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'group_name': '测试群',
            'sender_name': '测试用户',
            'user_message': '这是一条测试消息',
            'bot_response': '这是测试回复',
            'status': 'test',
            'received_at': datetime.now()
        }
        
        print(f"\n尝试写入测试记录...")
        success = feishu.add_record(test_record)
        
        if success:
            print(f"✅ 测试记录写入成功")
            return True
        else:
            print(f"❌ 测试记录写入失败")
            return False
    else:
        print(f"❌ Access Token 获取失败")
        return False


def test_dingtalk_connection():
    """测试钉钉连接"""
    print_header("测试钉钉连接")
    
    dingtalk = DingtalkBitable()
    
    if not dingtalk.is_configured():
        print("❌ 钉钉多维表格未配置")
        return False
    
    # 尝试获取 access_token
    token = dingtalk._get_access_token()
    
    if token:
        print(f"✅ Access Token 获取成功")
        print(f"   Token: {token[:20]}...")
        
        # 尝试写入一条测试记录
        test_record = {
            'request_id': 'test_' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'group_name': '测试群',
            'sender_name': '测试用户',
            'user_message': '这是一条测试消息',
            'bot_response': '这是测试回复',
            'status': 'test',
            'received_at': datetime.now()
        }
        
        print(f"\n尝试写入测试记录...")
        success = dingtalk.add_record(test_record)
        
        if success:
            print(f"✅ 测试记录写入成功")
            return True
        else:
            print(f"❌ 测试记录写入失败")
            return False
    else:
        print(f"❌ Access Token 获取失败")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='多维表格同步工具')
    parser.add_argument('action', choices=['sync', 'sync-conversations', 'test'],
                       help='操作类型：sync=同步消息, sync-conversations=同步对话, test=测试连接')
    parser.add_argument('--platform', choices=['feishu', 'dingtalk', 'both'],
                       default='both', help='平台选择')
    parser.add_argument('--db', default='data/data.db', help='数据库路径')
    parser.add_argument('--days', type=int, default=7, help='同步天数')
    
    args = parser.parse_args()
    
    print("\n" + "🔄 " * 20)
    print("  多维表格同步工具")
    print("🔄 " * 20)
    
    success = True
    
    if args.action == 'test':
        # 测试连接
        if args.platform in ['feishu', 'both']:
            if not test_feishu_connection():
                success = False
        
        if args.platform in ['dingtalk', 'both']:
            if not test_dingtalk_connection():
                success = False
    
    elif args.action == 'sync':
        # 同步消息级别数据
        if args.platform in ['feishu', 'both']:
            if not sync_to_feishu(args.db, args.days, sync_type='messages'):
                success = False
        
        if args.platform in ['dingtalk', 'both']:
            if not sync_to_dingtalk(args.db, args.days):
                success = False
    
    elif args.action == 'sync-conversations':
        # 同步对话级别数据
        if args.platform in ['feishu', 'both']:
            if not sync_to_feishu(args.db, args.days, sync_type='conversations'):
                success = False
        
        if args.platform in ['dingtalk', 'both']:
            # TODO: 实现钉钉对话同步
            print("⚠️  钉钉对话同步功能开发中...")
            pass
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 操作完成")
    else:
        print("⚠️  操作完成（部分失败）")
    print("=" * 60 + "\n")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

