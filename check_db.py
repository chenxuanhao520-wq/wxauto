#!/usr/bin/env python3
"""
Check Database Records
"""

# Force UTF-8 encoding
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import sqlite3

def check_database():
    """Check database records"""
    
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    
    # Check message count
    cursor.execute('SELECT COUNT(*) FROM messages')
    message_count = cursor.fetchone()[0]
    print(f"📊 消息总数: {message_count}")
    
    # Check session count
    cursor.execute('SELECT COUNT(*) FROM sessions')
    session_count = cursor.fetchone()[0]
    print(f"📊 会话总数: {session_count}")
    
    # Get latest messages
    cursor.execute('SELECT sender_name, user_message, received_at FROM messages ORDER BY received_at DESC LIMIT 5')
    rows = cursor.fetchall()
    
    print(f"\n📝 最新消息记录:")
    for i, row in enumerate(rows, 1):
        sender, message, received_at = row
        print(f"  {i}. {sender}: {message[:40]}...")
        print(f"     时间: {received_at}")
    
    # Get session summary
    cursor.execute('SELECT group_name, sender_name, turn_count, status FROM sessions ORDER BY created_at DESC LIMIT 3')
    sessions = cursor.fetchall()
    
    print(f"\n💬 最新会话:")
    for i, session in enumerate(sessions, 1):
        group, sender, turns, status = session
        print(f"  {i}. {group} - {sender} ({turns}轮, {status})")
    
    conn.close()
    
    print(f"\n✅ 数据库检查完成!")

if __name__ == "__main__":
    check_database()
