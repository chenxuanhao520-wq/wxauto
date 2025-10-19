#!/usr/bin/env python3
"""
微信历史记录导入工具
用于导入历史聊天记录，学习对话风格
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from adaptive_learning import HistoryImporter, UserProfiler, PersonalizedPromptGenerator
from storage.db import Database


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def import_history(file_path: str, target_groups: List[str] = None):
    """导入历史记录"""
    print_header("导入微信历史记录")
    
    importer = HistoryImporter()
    
    # 判断文件类型
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.db':
        # SQLite数据库
        print(f"正在从数据库导入: {file_path}")
        conversations = importer.import_from_wechat_backup(file_path, target_groups)
    
    elif file_ext == '.txt':
        # 文本文件
        print(f"正在从文本文件导入: {file_path}")
        conversations = importer.import_from_text(file_path)
    
    else:
        print(f"❌ 不支持的文件格式: {file_ext}")
        print("支持格式：.db（微信备份）, .txt（文本对话）")
        return
    
    if not conversations:
        print("❌ 未找到有效对话")
        return
    
    print(f"✅ 导入成功：{len(conversations)}条消息\n")
    
    # 提取Q&A对
    if isinstance(conversations[0], dict) and 'is_sent_by_me' in conversations[0]:
        print("正在提取Q&A对...")
        qa_pairs = importer.extract_qa_pairs(conversations)
        print(f"✅ 提取到{len(qa_pairs)}对对话\n")
    else:
        qa_pairs = conversations
    
    # 分析对话风格
    print("正在分析对话风格...")
    style = importer.analyze_conversation_style(qa_pairs, use_llm=False)
    
    print("\n对话风格分析结果：")
    print(f"  语气：{style.get('tone', 'N/A')}")
    print(f"  平均长度：{style.get('avg_length', 0)}字")
    print(f"  使用emoji：{'是' if style.get('uses_emoji') else '否'}")
    print(f"  称呼方式：{style.get('addressing', 'N/A')}")
    print(f"  常用词：{', '.join(style.get('common_phrases', [])[:10])}")
    
    # 保存风格配置
    import json
    style_file = "data/conversation_style.json"
    with open(style_file, 'w', encoding='utf-8') as f:
        json.dump(style, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 风格配置已保存：{style_file}")
    
    # 显示示例
    print("\n示例对话（用于Few-Shot学习）：\n")
    for i, qa in enumerate(qa_pairs[:3], 1):
        print(f"示例{i}：")
        print(f"  客户: {qa['question'][:50]}...")
        print(f"  客服: {qa['answer'][:50]}...")
        print()
    
    return qa_pairs, style


def build_user_profiles(qa_pairs: List[Dict]):
    """构建用户画像"""
    print_header("构建用户画像")
    
    db = Database("data/data.db")
    profiler = UserProfiler(db)
    
    # 按用户分组
    from collections import defaultdict
    by_user = defaultdict(list)
    
    for qa in qa_pairs:
        # 这里简化处理，实际需要从对话中识别user_id
        user_id = "historical_user"
        by_user[user_id].append({
            'user_message': qa['question'],
            'bot_response': qa['answer']
        })
    
    # 为每个用户构建画像
    for user_id, history in by_user.items():
        profile = profiler.auto_detect_features(user_id, history)
        print(f"✅ 用户画像已创建：{user_id}")
        print(f"   沟通风格：{profile.communication_style}")
        print(f"   技术水平：{profile.technical_level}")
        print()
    
    db.close()


def test_personalized_response(user_type: str = "vip"):
    """测试个性化回复"""
    print_header("测试个性化回复")
    
    from adaptive_learning import UserProfile, PersonalizedPromptGenerator
    
    # 创建测试用户画像
    test_profiles = {
        'vip': UserProfile(
            user_id='vip_customer',
            user_name='张总',
            customer_type='vip',
            company_name='某某充电站运营公司',
            communication_style='formal',
            technical_level='high'
        ),
        'regular': UserProfile(
            user_id='regular_customer',
            user_name='李四',
            customer_type='regular',
            communication_style='friendly',
            technical_level='medium'
        ),
        'newbie': UserProfile(
            user_id='new_customer',
            customer_type='new',
            communication_style='friendly',
            technical_level='low'
        )
    }
    
    profile = test_profiles.get(user_type, test_profiles['regular'])
    
    # 生成个性化Prompt
    generator = PersonalizedPromptGenerator()
    prompt = generator.generate(profile)
    
    print(f"用户类型：{user_type}")
    print(f"用户画像：{profile.customer_type} / {profile.technical_level}")
    print(f"\n生成的个性化System Prompt：\n")
    print(prompt)
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='微信历史记录导入工具')
    parser.add_argument('action', choices=['import', 'build-profiles', 'test'],
                       help='操作类型')
    parser.add_argument('--file', help='历史记录文件路径')
    parser.add_argument('--groups', nargs='+', help='目标群聊列表')
    parser.add_argument('--user-type', choices=['vip', 'regular', 'newbie'],
                       default='regular', help='测试用户类型')
    
    args = parser.parse_args()
    
    print("\n" + "📚 " * 20)
    print("  微信历史记录导入工具")
    print("📚 " * 20)
    
    if args.action == 'import':
        if not args.file:
            print("❌ 请指定 --file 参数")
            sys.exit(1)
        
        qa_pairs, style = import_history(args.file, args.groups)
        
        # 询问是否构建用户画像
        print("\n是否要构建用户画像？")
        response = input("[Y/n]: ").strip().lower()
        
        if response != 'n':
            build_user_profiles(qa_pairs)
    
    elif args.action == 'build-profiles':
        print("此功能需要先导入历史记录")
        print("请运行：python import_wechat_history.py import --file your_backup.db")
    
    elif args.action == 'test':
        test_personalized_response(args.user_type)


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

