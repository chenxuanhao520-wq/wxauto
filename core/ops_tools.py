#!/usr/bin/env python3
"""
运维工具：健康检查、日志轮转、性能统计
"""

# 强制 UTF-8 编码
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3

sys.path.insert(0, str(Path(__file__).parent))

from modules.storage.db import Database
from modules.ai_gateway.gateway import AIGateway

logger = logging.getLogger(__name__)


def health_check(db_path: str = "data/data.db"):
    """系统健康检查"""
    print("\n" + "=" * 60)
    print("🏥 系统健康检查")
    print("=" * 60)
    
    checks = {
        'database': False,
        'ai_gateway': False,
        'knowledge_base': False,
        'logs': False
    }
    
    # 1. 数据库检查
    print("\n[1/4] 检查数据库...")
    try:
        db = Database(db_path)
        conn = db.connect()
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('sessions', 'messages', 'knowledge_chunks')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        if len(tables) >= 3:
            print("  ✅ 数据库正常")
            checks['database'] = True
            
            # 统计数据
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE status='active'")
            active_sessions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM messages WHERE received_at >= datetime('now', '-24 hours')")
            messages_24h = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM knowledge_chunks")
            kb_count = cursor.fetchone()[0]
            
            print(f"     - 活跃会话: {active_sessions}")
            print(f"     - 24h消息: {messages_24h}")
            print(f"     - 知识块: {kb_count}")
        else:
            print(f"  ❌ 数据库表不完整: {tables}")
        
        db.close()
    except Exception as e:
        print(f"  ❌ 数据库检查失败: {e}")
    
    # 2. AI 网关检查
    print("\n[2/4] 检查 AI 网关...")
    try:
        gateway = AIGateway(
            primary_provider="openai",
            fallback_provider="deepseek",
            enable_fallback=True
        )
        
        status = gateway.health_check()
        if status['available']:
            print("  ✅ AI 网关可用")
            for provider in status['providers']:
                icon = "✓" if provider['available'] else "✗"
                print(f"     {icon} {provider['name']}")
            checks['ai_gateway'] = True
        else:
            print("  ❌ AI 网关不可用")
    except Exception as e:
        print(f"  ⚠️  AI 网关检查跳过: {e}")
    
    # 3. 知识库检查
    print("\n[3/4] 检查知识库...")
    try:
        from modules.rag.retriever import Retriever
        retriever = Retriever()
        retriever.load_knowledge_base(db_path)
        
        if retriever._corpus:
            print(f"  ✅ 知识库已加载: {len(retriever._corpus)} 个知识块")
            checks['knowledge_base'] = True
        else:
            print("  ⚠️  知识库为空")
    except Exception as e:
        print(f"  ❌ 知识库检查失败: {e}")
    
    # 4. 日志文件检查
    print("\n[4/4] 检查日志文件...")
    log_file = Path("logs/app.log")
    if log_file.exists():
        size_mb = log_file.stat().st_size / (1024 * 1024)
        print(f"  ✅ 日志文件存在: {size_mb:.2f} MB")
        
        if size_mb > 100:
            print(f"  ⚠️  日志文件过大，建议轮转")
        
        checks['logs'] = True
    else:
        print("  ⚠️  日志文件不存在")
    
    # 总结
    print("\n" + "=" * 60)
    passed = sum(checks.values())
    total = len(checks)
    
    if passed == total:
        print(f"✅ 健康检查通过 ({passed}/{total})")
        return 0
    else:
        print(f"⚠️  健康检查部分失败 ({passed}/{total})")
        return 1


def rotate_logs(log_dir: str = "logs", max_size_mb: int = 50):
    """日志轮转"""
    print("\n" + "=" * 60)
    print("📝 日志轮转")
    print("=" * 60)
    
    log_path = Path(log_dir)
    if not log_path.exists():
        print("❌ 日志目录不存在")
        return
    
    log_file = log_path / "app.log"
    if not log_file.exists():
        print("❌ 日志文件不存在")
        return
    
    size_mb = log_file.stat().st_size / (1024 * 1024)
    print(f"\n当前日志大小: {size_mb:.2f} MB")
    print(f"轮转阈值: {max_size_mb} MB")
    
    if size_mb < max_size_mb:
        print("\n✅ 日志大小正常，无需轮转")
        return
    
    # 执行轮转
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = log_path / f"app_{timestamp}.log"
    
    try:
        log_file.rename(archive_name)
        print(f"\n✅ 日志已归档: {archive_name.name}")
        
        # 创建新的日志文件
        log_file.touch()
        print(f"✅ 新日志文件已创建")
        
    except Exception as e:
        print(f"\n❌ 日志轮转失败: {e}")


def performance_report(db_path: str = "data/data.db", days: int = 7):
    """性能统计报告"""
    print("\n" + "=" * 60)
    print(f"📊 性能统计报告（最近 {days} 天）")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 1. 总体统计
        print("\n【总体统计】")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status='answered' THEN 1 END) as answered,
                COUNT(CASE WHEN branch='handoff' THEN 1 END) as handoff,
                AVG(latency_total_ms) as avg_latency,
                AVG(confidence) as avg_confidence
            FROM messages
            WHERE received_at >= ?
        """, (cutoff_date,))
        
        row = cursor.fetchone()
        total, answered, handoff, avg_latency, avg_conf = row
        
        if total > 0:
            answer_rate = (answered / total) * 100
            handoff_rate = (handoff / total) * 100
            
            print(f"  总消息数: {total}")
            print(f"  已回答: {answered} ({answer_rate:.1f}%)")
            print(f"  转人工: {handoff} ({handoff_rate:.1f}%)")
            print(f"  平均时延: {avg_latency:.0f} ms" if avg_latency else "  平均时延: N/A")
            print(f"  平均置信度: {avg_conf:.2f}" if avg_conf else "  平均置信度: N/A")
        else:
            print("  无数据")
        
        # 2. 按分支统计
        print("\n【分支分布】")
        cursor.execute("""
            SELECT branch, COUNT(*) as count
            FROM messages
            WHERE received_at >= ?
            GROUP BY branch
            ORDER BY count DESC
        """, (cutoff_date,))
        
        for row in cursor.fetchall():
            branch, count = row
            if total > 0:
                pct = (count / total) * 100
                print(f"  {branch or 'unknown'}: {count} ({pct:.1f}%)")
        
        # 3. 按提供商统计
        print("\n【AI 提供商】")
        cursor.execute("""
            SELECT provider, COUNT(*) as count,
                   AVG(token_total) as avg_tokens,
                   AVG(latency_generation_ms) as avg_gen_latency
            FROM messages
            WHERE received_at >= ? AND provider IS NOT NULL
            GROUP BY provider
            ORDER BY count DESC
        """, (cutoff_date,))
        
        for row in cursor.fetchall():
            provider, count, avg_tokens, avg_gen_latency = row
            print(f"  {provider}:")
            print(f"    请求数: {count}")
            print(f"    平均 token: {avg_tokens:.0f}" if avg_tokens else "    平均 token: N/A")
            print(f"    平均生成时延: {avg_gen_latency:.0f} ms" if avg_gen_latency else "    平均生成时延: N/A")
        
        # 4. 每日趋势
        print("\n【每日趋势】")
        cursor.execute("""
            SELECT DATE(received_at) as date, COUNT(*) as count
            FROM messages
            WHERE received_at >= ?
            GROUP BY DATE(received_at)
            ORDER BY date DESC
            LIMIT 7
        """, (cutoff_date,))
        
        for row in cursor.fetchall():
            date, count = row
            print(f"  {date}: {count} 条消息")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ 统计报告生成失败: {e}")


def cleanup_old_data(db_path: str = "data/data.db", days: int = 90):
    """清理旧数据"""
    print("\n" + "=" * 60)
    print(f"🗑️  清理 {days} 天前的数据")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 清理过期会话
        cursor.execute("""
            DELETE FROM sessions
            WHERE status='expired' AND last_active_at < ?
        """, (cutoff_date,))
        
        deleted_sessions = cursor.rowcount
        print(f"  清理会话: {deleted_sessions} 条")
        
        # 清理旧消息（保留统计信息）
        cursor.execute("""
            DELETE FROM messages
            WHERE received_at < ? AND status != 'failed'
        """, (cutoff_date,))
        
        deleted_messages = cursor.rowcount
        print(f"  清理消息: {deleted_messages} 条")
        
        # 清理速率限制记录
        cursor.execute("""
            DELETE FROM rate_limits
            WHERE window_start < ?
        """, (cutoff_date,))
        
        deleted_limits = cursor.rowcount
        print(f"  清理限流记录: {deleted_limits} 条")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ 清理完成")
        
    except Exception as e:
        print(f"\n❌ 清理失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='运维工具')
    parser.add_argument('action', choices=['health', 'rotate', 'report', 'cleanup'],
                       help='操作类型')
    parser.add_argument('--db', default='data/data.db', help='数据库路径')
    parser.add_argument('--days', type=int, default=7, help='统计天数或清理天数')
    parser.add_argument('--max-log-size', type=int, default=50, help='日志轮转阈值（MB）')
    
    args = parser.parse_args()
    
    if args.action == 'health':
        exit_code = health_check(args.db)
        sys.exit(exit_code)
    
    elif args.action == 'rotate':
        rotate_logs(max_size_mb=args.max_log_size)
    
    elif args.action == 'report':
        performance_report(args.db, args.days)
    
    elif args.action == 'cleanup':
        cleanup_old_data(args.db, args.days)


if __name__ == "__main__":
    main()

