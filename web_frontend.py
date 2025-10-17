#!/usr/bin/env python3
"""
Web 前端界面 - 微信客服中台管理面板
提供可视化的配置管理、系统监控、消息查看等功能
"""

# 强制 UTF-8 编码
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import json
import yaml
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
    from flask_socketio import SocketIO, emit
except ImportError:
    print("需要安装 Flask 和 Flask-SocketIO:")
    print("pip install flask flask-socketio")
    sys.exit(1)

from storage.db import Database
from ai_gateway.gateway import AIGateway
from adapters.wxauto_adapter import FakeWxAdapter
from customer_manager import customer_manager
from sync_manager import sync_manager

# 创建 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'wechat-customer-service-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
bot_instance = None
config_data = {}
db_instance = None

def load_config():
    """加载配置文件"""
    global config_data
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
    except FileNotFoundError:
        config_data = {}
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        config_data = {}

def save_config():
    """保存配置文件"""
    try:
        with open('config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False

def get_database():
    """获取数据库实例"""
    global db_instance
    if db_instance is None:
        db_instance = Database('data/data.db')
    return db_instance

# 路由定义
@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/config')
def config_page():
    """配置页面"""
    load_config()
    return render_template('config.html', config=config_data)

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """配置 API"""
    global config_data
    
    if request.method == 'GET':
        load_config()
        return jsonify(config_data)
    
    elif request.method == 'POST':
        try:
            new_config = request.json
            config_data.update(new_config)
            
            if save_config():
                return jsonify({"success": True, "message": "配置保存成功"})
            else:
                return jsonify({"success": False, "message": "配置保存失败"})
        except Exception as e:
            return jsonify({"success": False, "message": f"配置更新失败: {e}"})

@app.route('/api/keys', methods=['GET', 'POST'])
def api_keys():
    """API 密钥管理"""
    if request.method == 'GET':
        # 从环境变量读取密钥（不显示完整值）
        keys = {}
        key_mappings = {
            'OPENAI_API_KEY': 'OpenAI',
            'DEEPSEEK_API_KEY': 'DeepSeek',
            'CLAUDE_API_KEY': 'Claude',
            'QWEN_API_KEY': '通义千问',
            'ERNIE_API_KEY': '文心一言',
            'GEMINI_API_KEY': 'Gemini',
            'MOONSHOT_API_KEY': 'Moonshot',
            'FEISHU_APP_ID': '飞书 App ID',
            'FEISHU_APP_SECRET': '飞书 App Secret',
            'FEISHU_BITABLE_TOKEN': '飞书多维表格 Token',
            'FEISHU_TABLE_ID': '飞书表格 ID',
            'DINGTALK_APP_KEY': '钉钉 App Key',
            'DINGTALK_APP_SECRET': '钉钉 App Secret',
            'DINGTALK_BASE_ID': '钉钉 Base ID',
            'DINGTALK_TABLE_ID': '钉钉表格 ID'
        }
        
        for env_key, display_name in key_mappings.items():
            value = os.getenv(env_key, '')
            keys[env_key] = {
                'name': display_name,
                'value': value[:8] + '...' if value and len(value) > 8 else value,
                'has_value': bool(value)
            }
        
        return jsonify(keys)
    
    elif request.method == 'POST':
        try:
            key_data = request.json
            key_name = key_data.get('key')
            key_value = key_data.get('value')
            
            if not key_name or not key_value:
                return jsonify({"success": False, "message": "密钥名称和值不能为空"})
            
            # 设置环境变量
            os.environ[key_name] = key_value
            
            return jsonify({"success": True, "message": "密钥保存成功"})
        except Exception as e:
            return jsonify({"success": False, "message": f"密钥保存失败: {e}"})

@app.route('/monitor')
def monitor_page():
    """监控页面"""
    return render_template('monitor.html')

@app.route('/api/status')
def api_status():
    """系统状态 API"""
    try:
        db = get_database()
        
        # 获取统计数据
        stats = {}
        
        # 消息统计
        with db.connect() as conn:
            cursor = conn.cursor()
            
            # 今日消息数
            cursor.execute("""
                SELECT COUNT(*) FROM messages 
                WHERE DATE(received_at) = DATE('now')
            """)
            stats['messages_today'] = cursor.fetchone()[0]
            
            # 总会话数
            cursor.execute("SELECT COUNT(*) FROM sessions")
            stats['total_sessions'] = cursor.fetchone()[0]
            
            # 活跃会话数
            cursor.execute("""
                SELECT COUNT(*) FROM sessions 
                WHERE status = 'active' AND expires_at > datetime('now')
            """)
            stats['active_sessions'] = cursor.fetchone()[0]
            
            # 最近消息
            cursor.execute("""
                SELECT sender_name, user_message, received_at 
                FROM messages 
                ORDER BY received_at DESC 
                LIMIT 5
            """)
            stats['recent_messages'] = cursor.fetchall()
        
        # AI 网关状态
        try:
            ai_gateway = AIGateway()
            stats['ai_status'] = 'available' if ai_gateway.primary_provider else 'unavailable'
        except:
            stats['ai_status'] = 'unavailable'
        
        # 知识库状态
        stats['knowledge_base_count'] = 0  # 可以从 RAG 获取
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/logs')
def logs_page():
    """日志页面"""
    return render_template('logs.html')

@app.route('/api/logs')
def api_logs():
    """消息日志 API"""
    try:
        db = get_database()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        offset = (page - 1) * per_page
        
        with db.connect() as conn:
            cursor = conn.cursor()
            
            # 获取消息日志
            cursor.execute("""
                SELECT id, sender_name, user_message, bot_response, 
                       confidence, status, received_at, responded_at
                FROM messages 
                ORDER BY received_at DESC 
                LIMIT ? OFFSET ?
            """, (per_page, offset))
            
            messages = cursor.fetchall()
            
            # 获取总数
            cursor.execute("SELECT COUNT(*) FROM messages")
            total = cursor.fetchone()[0]
            
            return jsonify({
                'messages': [
                    {
                        'id': msg[0],
                        'sender': msg[1],
                        'user_message': msg[2],
                        'bot_response': msg[3],
                        'confidence': msg[4],
                        'status': msg[5],
                        'received_at': msg[6],
                        'responded_at': msg[7]
                    }
                    for msg in messages
                ],
                'total': total,
                'page': page,
                'per_page': per_page
            })
            
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/test')
def test_page():
    """测试页面"""
    return render_template('test.html')

@app.route('/api/test/message', methods=['POST'])
def api_test_message():
    """测试消息 API"""
    try:
        data = request.json
        group = data.get('group', '测试群')
        sender = data.get('sender', '测试用户')
        content = data.get('content', '@小助手 测试消息')
        
        # 创建假适配器并注入消息
        adapter = FakeWxAdapter(whitelisted_groups=[group])
        adapter.inject_message(
            group_name=group,
            sender_name=sender,
            content=content,
            is_at_me=True
        )
        
        # 通过 WebSocket 通知前端
        socketio.emit('test_message_sent', {
            'group': group,
            'sender': sender,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({"success": True, "message": "测试消息已发送"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"测试失败: {e}"})

@app.route('/customers')
def customers_page():
    """客户管理页面"""
    return render_template('customers.html')

@app.route('/api/customers')
def api_customers():
    """客户列表 API"""
    try:
        group_name = request.args.get('group')
        limit = request.args.get('limit', 100, type=int)
        
        customers = customer_manager.get_customer_list(group_name, limit)
        
        return jsonify({
            'customers': [
                {
                    'customer_id': c.customer_id,
                    'name': c.name,
                    'group_name': c.group_name,
                    'group_type': c.group_type,
                    'registration_time': c.registration_time.isoformat(),
                    'last_active': c.last_active.isoformat(),
                    'total_questions': c.total_questions,
                    'solved_questions': c.solved_questions,
                    'handoff_count': c.handoff_count,
                    'tags': c.tags,
                    'notes': c.notes,
                    'priority': c.priority
                }
                for c in customers
            ]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/customers/<customer_id>', methods=['GET', 'PUT'])
def api_customer_detail(customer_id):
    """客户详情 API"""
    try:
        customer = customer_manager.get_customer(customer_id)
        if not customer:
            return jsonify({"error": "客户不存在"}), 404
        
        if request.method == 'GET':
            return jsonify({
                'customer_id': customer.customer_id,
                'name': customer.name,
                'group_name': customer.group_name,
                'group_type': customer.group_type,
                'registration_time': customer.registration_time.isoformat(),
                'last_active': customer.last_active.isoformat(),
                'total_questions': customer.total_questions,
                'solved_questions': customer.solved_questions,
                'handoff_count': customer.handoff_count,
                'tags': customer.tags,
                'notes': customer.notes,
                'priority': customer.priority
            })
        
        elif request.method == 'PUT':
            data = request.json
            customer.notes = data.get('notes', customer.notes)
            customer.priority = data.get('priority', customer.priority)
            customer.tags = data.get('tags', customer.tags)
            
            customer_manager._save_customer(customer)
            return jsonify({"success": True, "message": "客户信息已更新"})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/customers/register', methods=['POST'])
def api_register_customer():
    """注册新客户 API"""
    try:
        data = request.json
        name = data.get('name')
        group_name = data.get('group_name')
        notes = data.get('notes', '')
        priority = data.get('priority', 3)
        
        if not name or not group_name:
            return jsonify({"success": False, "message": "姓名和群聊名称不能为空"})
        
        customer_id = customer_manager.register_customer(name, group_name, notes, priority)
        
        return jsonify({
            "success": True, 
            "message": "客户注册成功",
            "customer_id": customer_id
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"注册失败: {e}"})

@app.route('/api/customers/stats')
def api_customer_stats():
    """客户统计 API"""
    try:
        stats = customer_manager.get_customer_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/sync/status')
def api_sync_status():
    """同步状态 API"""
    try:
        status = sync_manager.get_sync_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/sync/manual', methods=['POST'])
def api_manual_sync():
    """手动同步 API"""
    try:
        data = request.json or {}
        direction = data.get('direction', 'both')  # from, to, both
        
        result = sync_manager.manual_sync(direction)
        
        return jsonify({
            "success": True,
            "message": "同步完成",
            "result": result
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"同步失败: {e}"})

@app.route('/api/sync/auto', methods=['POST'])
def api_auto_sync():
    """自动同步控制 API"""
    try:
        data = request.json or {}
        action = data.get('action')  # start, stop
        
        if action == 'start':
            sync_manager.start_auto_sync()
            return jsonify({"success": True, "message": "自动同步已启动"})
        elif action == 'stop':
            sync_manager.stop_auto_sync()
            return jsonify({"success": True, "message": "自动同步已停止"})
        else:
            return jsonify({"success": False, "message": "无效的操作"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"操作失败: {e}"})

# WebSocket 事件
@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print('客户端已连接')
    emit('status', {'message': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    print('客户端已断开连接')

@socketio.on('request_status')
def handle_status_request():
    """处理状态请求"""
    try:
        # 发送实时状态
        stats = {}
        db = get_database()
        
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE DATE(received_at) = DATE('now')")
            stats['messages_today'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'active'")
            stats['active_sessions'] = cursor.fetchone()[0]
        
        emit('status_update', stats)
        
    except Exception as e:
        emit('error', {'message': str(e)})

def create_templates():
    """创建 HTML 模板"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # 基础模板
    base_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}微信客服中台{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        .sidebar { min-height: 100vh; background: #f8f9fa; }
        .main-content { padding: 20px; }
        .status-card { border-left: 4px solid #007bff; }
        .success-card { border-left: 4px solid #28a745; }
        .warning-card { border-left: 4px solid #ffc107; }
        .danger-card { border-left: 4px solid #dc3545; }
        .config-section { margin-bottom: 30px; }
        .key-input { font-family: monospace; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- 侧边栏 -->
            <div class="col-md-2 sidebar p-3">
                <h5><i class="bi bi-robot"></i> 客服中台</h5>
                <hr>
                <ul class="nav nav-pills flex-column">
                    <li class="nav-item">
                        <a class="nav-link {% if request.endpoint == 'index' %}active{% endif %}" href="{{ url_for('index') }}">
                            <i class="bi bi-house"></i> 首页
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.endpoint == 'config_page' %}active{% endif %}" href="{{ url_for('config_page') }}">
                            <i class="bi bi-gear"></i> 配置管理
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.endpoint == 'monitor_page' %}active{% endif %}" href="{{ url_for('monitor_page') }}">
                            <i class="bi bi-graph-up"></i> 系统监控
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.endpoint == 'logs_page' %}active{% endif %}" href="{{ url_for('logs_page') }}">
                            <i class="bi bi-chat-text"></i> 消息日志
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.endpoint == 'customers_page' %}active{% endif %}" href="{{ url_for('customers_page') }}">
                            <i class="bi bi-people"></i> 客户管理
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.endpoint == 'test_page' %}active{% endif %}" href="{{ url_for('test_page') }}">
                            <i class="bi bi-bug"></i> 功能测试
                        </a>
                    </li>
                </ul>
            </div>
            
            <!-- 主内容区 -->
            <div class="col-md-10 main-content">
                {% block content %}{% endblock %}
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
    
    # 首页模板
    index_template = '''{% extends "base.html" %}
{% block title %}首页 - 微信客服中台{% endblock %}
{% block content %}
<div class="row">
    <div class="col-12">
        <h1><i class="bi bi-house"></i> 系统概览</h1>
        <hr>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card status-card">
            <div class="card-body">
                <h5 class="card-title"><i class="bi bi-chat-dots"></i> 今日消息</h5>
                <h3 id="messages-today">-</h3>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card success-card">
            <div class="card-body">
                <h5 class="card-title"><i class="bi bi-people"></i> 活跃会话</h5>
                <h3 id="active-sessions">-</h3>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card warning-card">
            <div class="card-body">
                <h5 class="card-title"><i class="bi bi-robot"></i> AI 状态</h5>
                <h3 id="ai-status">-</h3>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card danger-card">
            <div class="card-body">
                <h5 class="card-title"><i class="bi bi-book"></i> 知识库</h5>
                <h3 id="kb-count">-</h3>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-clock-history"></i> 最近消息</h5>
            </div>
            <div class="card-body">
                <div id="recent-messages">
                    <p class="text-muted">加载中...</p>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-tools"></i> 快速操作</h5>
            </div>
            <div class="card-body">
                <div class="d-grid gap-2">
                    <a href="{{ url_for('config_page') }}" class="btn btn-primary">
                        <i class="bi bi-gear"></i> 配置管理
                    </a>
                    <a href="{{ url_for('monitor_page') }}" class="btn btn-info">
                        <i class="bi bi-graph-up"></i> 系统监控
                    </a>
                    <a href="{{ url_for('test_page') }}" class="btn btn-success">
                        <i class="bi bi-bug"></i> 功能测试
                    </a>
                    <a href="{{ url_for('logs_page') }}" class="btn btn-secondary">
                        <i class="bi bi-chat-text"></i> 查看日志
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    const socket = io();
    
    // 连接成功
    socket.on('connect', function() {
        console.log('WebSocket 连接成功');
        socket.emit('request_status');
    });
    
    // 接收状态更新
    socket.on('status_update', function(data) {
        document.getElementById('messages-today').textContent = data.messages_today || 0;
        document.getElementById('active-sessions').textContent = data.active_sessions || 0;
    });
    
    // 加载初始数据
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('messages-today').textContent = data.messages_today || 0;
            document.getElementById('active-sessions').textContent = data.active_sessions || 0;
            document.getElementById('ai-status').textContent = data.ai_status === 'available' ? '正常' : '异常';
            document.getElementById('kb-count').textContent = data.knowledge_base_count || 0;
            
            // 显示最近消息
            const messagesDiv = document.getElementById('recent-messages');
            if (data.recent_messages && data.recent_messages.length > 0) {
                messagesDiv.innerHTML = data.recent_messages.map(msg => 
                    `<div class="mb-2">
                        <strong>${msg[0]}:</strong> ${msg[1].substring(0, 50)}...
                        <small class="text-muted">${new Date(msg[2]).toLocaleString()}</small>
                    </div>`
                ).join('');
            } else {
                messagesDiv.innerHTML = '<p class="text-muted">暂无消息</p>';
            }
        })
        .catch(error => {
            console.error('加载状态失败:', error);
        });
    
    // 定期更新状态
    setInterval(() => {
        socket.emit('request_status');
    }, 10000);
</script>
{% endblock %}'''
    
    # 配置页面模板
    config_template = '''{% extends "base.html" %}
{% block title %}配置管理 - 微信客服中台{% endblock %}
{% block content %}
<div class="row">
    <div class="col-12">
        <h1><i class="bi bi-gear"></i> 配置管理</h1>
        <hr>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card config-section">
            <div class="card-header">
                <h5><i class="bi bi-key"></i> API 密钥配置</h5>
            </div>
            <div class="card-body">
                <form id="api-keys-form">
                    <div class="mb-3">
                        <label class="form-label">OpenAI API Key</label>
                        <div class="input-group">
                            <input type="password" class="form-control key-input" id="openai-key" placeholder="sk-...">
                            <button class="btn btn-outline-secondary" type="button" onclick="toggleVisibility('openai-key')">
                                <i class="bi bi-eye"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">DeepSeek API Key</label>
                        <div class="input-group">
                            <input type="password" class="form-control key-input" id="deepseek-key" placeholder="sk-...">
                            <button class="btn btn-outline-secondary" type="button" onclick="toggleVisibility('deepseek-key')">
                                <i class="bi bi-eye"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">通义千问 API Key</label>
                        <div class="input-group">
                            <input type="password" class="form-control key-input" id="qwen-key" placeholder="sk-...">
                            <button class="btn btn-outline-secondary" type="button" onclick="toggleVisibility('qwen-key')">
                                <i class="bi bi-eye"></i>
                            </button>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check"></i> 保存 API 密钥
                    </button>
                </form>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card config-section">
            <div class="card-header">
                <h5><i class="bi bi-table"></i> 飞书多维表格</h5>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <label class="form-label">飞书 App ID</label>
                    <input type="text" class="form-control key-input" id="feishu-app-id" placeholder="cli_...">
                </div>
                
                <div class="mb-3">
                    <label class="form-label">飞书 App Secret</label>
                    <input type="password" class="form-control key-input" id="feishu-app-secret">
                </div>
                
                <div class="mb-3">
                    <label class="form-label">多维表格 Token</label>
                    <input type="text" class="form-control key-input" id="feishu-bitable-token" placeholder="bascn...">
                </div>
                
                <div class="mb-3">
                    <label class="form-label">表格 ID</label>
                    <input type="text" class="form-control key-input" id="feishu-table-id" placeholder="tbl...">
                </div>
                
                <button type="button" class="btn btn-primary" onclick="saveFeishuConfig()">
                    <i class="bi bi-check"></i> 保存飞书配置
                </button>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-6">
        <div class="card config-section">
            <div class="card-header">
                <h5><i class="bi bi-table"></i> 钉钉多维表格</h5>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <label class="form-label">钉钉 App Key</label>
                    <input type="text" class="form-control key-input" id="dingtalk-app-key" placeholder="dingtalk...">
                </div>
                
                <div class="mb-3">
                    <label class="form-label">钉钉 App Secret</label>
                    <input type="password" class="form-control key-input" id="dingtalk-app-secret">
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Base ID</label>
                    <input type="text" class="form-control key-input" id="dingtalk-base-id">
                </div>
                
                <div class="mb-3">
                    <label class="form-label">表格 ID</label>
                    <input type="text" class="form-control key-input" id="dingtalk-table-id">
                </div>
                
                <button type="button" class="btn btn-primary" onclick="saveDingtalkConfig()">
                    <i class="bi bi-check"></i> 保存钉钉配置
                </button>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card config-section">
            <div class="card-header">
                <h5><i class="bi bi-sliders"></i> 系统配置</h5>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <label class="form-label">白名单群聊</label>
                    <textarea class="form-control" id="whitelisted-groups" rows="3" placeholder="每行一个群名"></textarea>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">检查间隔 (秒)</label>
                    <input type="number" class="form-control" id="check-interval" value="0.5" min="0.1" max="10" step="0.1">
                </div>
                
                <div class="mb-3">
                    <label class="form-label">最大 Token 数</label>
                    <input type="number" class="form-control" id="max-tokens" value="512" min="100" max="4000">
                </div>
                
                <button type="button" class="btn btn-success" onclick="saveSystemConfig()">
                    <i class="bi bi-check"></i> 保存系统配置
                </button>
            </div>
        </div>
    </div>
</div>

<!-- 提示消息 -->
<div id="alert-container"></div>
{% endblock %}

{% block scripts %}
<script>
    // 加载现有配置
    document.addEventListener('DOMContentLoaded', function() {
        loadApiKeys();
        loadSystemConfig();
    });
    
    // 加载 API 密钥
    function loadApiKeys() {
        fetch('/api/keys')
            .then(response => response.json())
            .then(data => {
                if (data.OPENAI_API_KEY) {
                    document.getElementById('openai-key').value = data.OPENAI_API_KEY.value;
                }
                if (data.DEEPSEEK_API_KEY) {
                    document.getElementById('deepseek-key').value = data.DEEPSEEK_API_KEY.value;
                }
                if (data.QWEN_API_KEY) {
                    document.getElementById('qwen-key').value = data.QWEN_API_KEY.value;
                }
                if (data.FEISHU_APP_ID) {
                    document.getElementById('feishu-app-id').value = data.FEISHU_APP_ID.value;
                }
                if (data.FEISHU_APP_SECRET) {
                    document.getElementById('feishu-app-secret').value = data.FEISHU_APP_SECRET.value;
                }
                if (data.FEISHU_BITABLE_TOKEN) {
                    document.getElementById('feishu-bitable-token').value = data.FEISHU_BITABLE_TOKEN.value;
                }
                if (data.FEISHU_TABLE_ID) {
                    document.getElementById('feishu-table-id').value = data.FEISHU_TABLE_ID.value;
                }
                if (data.DINGTALK_APP_KEY) {
                    document.getElementById('dingtalk-app-key').value = data.DINGTALK_APP_KEY.value;
                }
                if (data.DINGTALK_APP_SECRET) {
                    document.getElementById('dingtalk-app-secret').value = data.DINGTALK_APP_SECRET.value;
                }
                if (data.DINGTALK_BASE_ID) {
                    document.getElementById('dingtalk-base-id').value = data.DINGTALK_BASE_ID.value;
                }
                if (data.DINGTALK_TABLE_ID) {
                    document.getElementById('dingtalk-table-id').value = data.DINGTALK_TABLE_ID.value;
                }
            })
            .catch(error => {
                showAlert('加载配置失败: ' + error.message, 'danger');
            });
    }
    
    // 加载系统配置
    function loadSystemConfig() {
        fetch('/api/config')
            .then(response => response.json())
            .then(data => {
                if (data.wechat && data.wechat.whitelisted_groups) {
                    document.getElementById('whitelisted-groups').value = data.wechat.whitelisted_groups.join('\\n');
                }
                if (data.wechat && data.wechat.check_interval_ms) {
                    document.getElementById('check-interval').value = data.wechat.check_interval_ms / 1000;
                }
                if (data.llm && data.llm.max_tokens) {
                    document.getElementById('max-tokens').value = data.llm.max_tokens;
                }
            });
    }
    
    // 保存 API 密钥
    document.getElementById('api-keys-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const keys = {
            'OPENAI_API_KEY': document.getElementById('openai-key').value,
            'DEEPSEEK_API_KEY': document.getElementById('deepseek-key').value,
            'QWEN_API_KEY': document.getElementById('qwen-key').value
        };
        
        for (const [key, value] of Object.entries(keys)) {
            if (value) {
                saveApiKey(key, value);
            }
        }
    });
    
    // 保存单个 API 密钥
    function saveApiKey(keyName, keyValue) {
        fetch('/api/keys', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                key: keyName,
                value: keyValue
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, 'success');
            } else {
                showAlert(data.message, 'danger');
            }
        })
        .catch(error => {
            showAlert('保存失败: ' + error.message, 'danger');
        });
    }
    
    // 保存飞书配置
    function saveFeishuConfig() {
        const config = {
            'FEISHU_APP_ID': document.getElementById('feishu-app-id').value,
            'FEISHU_APP_SECRET': document.getElementById('feishu-app-secret').value,
            'FEISHU_BITABLE_TOKEN': document.getElementById('feishu-bitable-token').value,
            'FEISHU_TABLE_ID': document.getElementById('feishu-table-id').value
        };
        
        for (const [key, value] of Object.entries(config)) {
            if (value) {
                saveApiKey(key, value);
            }
        }
    }
    
    // 保存钉钉配置
    function saveDingtalkConfig() {
        const config = {
            'DINGTALK_APP_KEY': document.getElementById('dingtalk-app-key').value,
            'DINGTALK_APP_SECRET': document.getElementById('dingtalk-app-secret').value,
            'DINGTALK_BASE_ID': document.getElementById('dingtalk-base-id').value,
            'DINGTALK_TABLE_ID': document.getElementById('dingtalk-table-id').value
        };
        
        for (const [key, value] of Object.entries(config)) {
            if (value) {
                saveApiKey(key, value);
            }
        }
    }
    
    // 保存系统配置
    function saveSystemConfig() {
        const groups = document.getElementById('whitelisted-groups').value.split('\\n').filter(g => g.trim());
        const config = {
            wechat: {
                whitelisted_groups: groups,
                check_interval_ms: parseFloat(document.getElementById('check-interval').value) * 1000
            },
            llm: {
                max_tokens: parseInt(document.getElementById('max-tokens').value)
            }
        };
        
        fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, 'success');
            } else {
                showAlert(data.message, 'danger');
            }
        })
        .catch(error => {
            showAlert('保存失败: ' + error.message, 'danger');
        });
    }
    
    // 切换密码可见性
    function toggleVisibility(inputId) {
        const input = document.getElementById(inputId);
        const button = input.nextElementSibling;
        const icon = button.querySelector('i');
        
        if (input.type === 'password') {
            input.type = 'text';
            icon.className = 'bi bi-eye-slash';
        } else {
            input.type = 'password';
            icon.className = 'bi bi-eye';
        }
    }
    
    // 显示提示消息
    function showAlert(message, type) {
        const alertContainer = document.getElementById('alert-container');
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alertContainer.appendChild(alertDiv);
        
        // 3秒后自动消失
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }
</script>
{% endblock %}'''
    
    # 监控页面模板
    monitor_template = '''{% extends "base.html" %}
{% block title %}系统监控 - 微信客服中台{% endblock %}
{% block content %}
<div class="row">
    <div class="col-12">
        <h1><i class="bi bi-graph-up"></i> 系统监控</h1>
        <hr>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card status-card">
            <div class="card-body text-center">
                <h5 class="card-title">今日消息</h5>
                <h2 id="monitor-messages-today">-</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card success-card">
            <div class="card-body text-center">
                <h5 class="card-title">活跃会话</h5>
                <h2 id="monitor-active-sessions">-</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card warning-card">
            <div class="card-body text-center">
                <h5 class="card-title">AI 状态</h5>
                <h2 id="monitor-ai-status">-</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card danger-card">
            <div class="card-body text-center">
                <h5 class="card-title">知识库</h5>
                <h2 id="monitor-kb-count">-</h2>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-activity"></i> 实时状态</h5>
            </div>
            <div class="card-body">
                <div id="real-time-status">
                    <p class="text-muted">连接中...</p>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-info-circle"></i> 系统信息</h5>
            </div>
            <div class="card-body">
                <ul class="list-unstyled">
                    <li><strong>运行时间:</strong> <span id="uptime">-</span></li>
                    <li><strong>Python 版本:</strong> <span id="python-version">-</span></li>
                    <li><strong>数据库:</strong> <span id="db-status">正常</span></li>
                    <li><strong>最后更新:</strong> <span id="last-update">-</span></li>
                </ul>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    const socket = io();
    let startTime = new Date();
    
    // 连接成功
    socket.on('connect', function() {
        document.getElementById('real-time-status').innerHTML = '<p class="text-success">✅ WebSocket 连接正常</p>';
        socket.emit('request_status');
    });
    
    // 接收状态更新
    socket.on('status_update', function(data) {
        updateMonitorData(data);
        document.getElementById('last-update').textContent = new Date().toLocaleString();
    });
    
    // 更新监控数据
    function updateMonitorData(data) {
        document.getElementById('monitor-messages-today').textContent = data.messages_today || 0;
        document.getElementById('monitor-active-sessions').textContent = data.active_sessions || 0;
    }
    
    // 加载初始数据
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updateMonitorData(data);
            document.getElementById('monitor-ai-status').textContent = data.ai_status === 'available' ? '正常' : '异常';
            document.getElementById('monitor-kb-count').textContent = data.knowledge_base_count || 0;
        })
        .catch(error => {
            console.error('加载状态失败:', error);
        });
    
    // 更新运行时间
    function updateUptime() {
        const now = new Date();
        const uptime = now - startTime;
        const hours = Math.floor(uptime / (1000 * 60 * 60));
        const minutes = Math.floor((uptime % (1000 * 60 * 60)) / (1000 * 60));
        document.getElementById('uptime').textContent = `${hours}小时${minutes}分钟`;
    }
    
    // 定期更新
    setInterval(() => {
        socket.emit('request_status');
        updateUptime();
    }, 5000);
    
    // 初始更新
    updateUptime();
</script>
{% endblock %}'''
    
    # 日志页面模板
    logs_template = '''{% extends "base.html" %}
{% block title %}消息日志 - 微信客服中台{% endblock %}
{% block content %}
<div class="row">
    <div class="col-12">
        <h1><i class="bi bi-chat-text"></i> 消息日志</h1>
        <hr>
    </div>
</div>

<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-list"></i> 消息记录</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>发送者</th>
                                <th>用户消息</th>
                                <th>机器人回复</th>
                                <th>置信度</th>
                                <th>状态</th>
                                <th>时间</th>
                            </tr>
                        </thead>
                        <tbody id="messages-table">
                            <tr>
                                <td colspan="7" class="text-center">加载中...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <!-- 分页 -->
                <nav>
                    <ul class="pagination justify-content-center" id="pagination">
                    </ul>
                </nav>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    let currentPage = 1;
    const perPage = 20;
    
    // 加载消息日志
    function loadMessages(page = 1) {
        fetch(`/api/logs?page=${page}&per_page=${perPage}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                displayMessages(data.messages);
                updatePagination(data.total, page, perPage);
                currentPage = page;
            })
            .catch(error => {
                console.error('加载消息失败:', error);
                document.getElementById('messages-table').innerHTML = 
                    '<tr><td colspan="7" class="text-center text-danger">加载失败: ' + error.message + '</td></tr>';
            });
    }
    
    // 显示消息
    function displayMessages(messages) {
        const tbody = document.getElementById('messages-table');
        
        if (messages.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">暂无消息记录</td></tr>';
            return;
        }
        
        tbody.innerHTML = messages.map(msg => `
            <tr>
                <td>${msg.id}</td>
                <td>${msg.sender || '未知'}</td>
                <td title="${msg.user_message}">${msg.user_message.substring(0, 30)}${msg.user_message.length > 30 ? '...' : ''}</td>
                <td title="${msg.bot_response}">${msg.bot_response ? msg.bot_response.substring(0, 30) + (msg.bot_response.length > 30 ? '...' : '') : '-'}</td>
                <td>${msg.confidence ? msg.confidence.toFixed(2) : '-'}</td>
                <td><span class="badge bg-${getStatusColor(msg.status)}">${msg.status || '未知'}</span></td>
                <td>${new Date(msg.received_at).toLocaleString()}</td>
            </tr>
        `).join('');
    }
    
    // 获取状态颜色
    function getStatusColor(status) {
        switch(status) {
            case 'answered': return 'success';
            case 'handoff': return 'warning';
            case 'error': return 'danger';
            default: return 'secondary';
        }
    }
    
    // 更新分页
    function updatePagination(total, currentPage, perPage) {
        const totalPages = Math.ceil(total / perPage);
        const pagination = document.getElementById('pagination');
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let paginationHTML = '';
        
        // 上一页
        if (currentPage > 1) {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="loadMessages(${currentPage - 1})">上一页</a></li>`;
        }
        
        // 页码
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `<li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadMessages(${i})">${i}</a>
            </li>`;
        }
        
        // 下一页
        if (currentPage < totalPages) {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="loadMessages(${currentPage + 1})">下一页</a></li>`;
        }
        
        pagination.innerHTML = paginationHTML;
    }
    
    // 页面加载时获取消息
    document.addEventListener('DOMContentLoaded', function() {
        loadMessages(1);
    });
</script>
{% endblock %}'''
    
    # 测试页面模板
    test_template = '''{% extends "base.html" %}
{% block title %}功能测试 - 微信客服中台{% endblock %}
{% block content %}
<div class="row">
    <div class="col-12">
        <h1><i class="bi bi-bug"></i> 功能测试</h1>
        <hr>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-chat"></i> 发送测试消息</h5>
            </div>
            <div class="card-body">
                <form id="test-message-form">
                    <div class="mb-3">
                        <label class="form-label">群聊名称</label>
                        <input type="text" class="form-control" id="test-group" value="技术支持群" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">发送者</label>
                        <input type="text" class="form-control" id="test-sender" value="测试用户" required>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">消息内容</label>
                        <textarea class="form-control" id="test-content" rows="3" required>@小助手 这是一个测试消息，请回复我。</textarea>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-send"></i> 发送测试消息
                    </button>
                </form>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-list-check"></i> 测试结果</h5>
            </div>
            <div class="card-body">
                <div id="test-results">
                    <p class="text-muted">暂无测试结果</p>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-gear"></i> 快速测试</h5>
            </div>
            <div class="card-body">
                <div class="d-grid gap-2">
                    <button class="btn btn-outline-primary" onclick="quickTest('普通问题')">
                        <i class="bi bi-question-circle"></i> 普通问题测试
                    </button>
                    <button class="btn btn-outline-warning" onclick="quickTest('禁答域问题')">
                        <i class="bi bi-exclamation-triangle"></i> 禁答域测试
                    </button>
                    <button class="btn btn-outline-info" onclick="quickTest('管理指令')">
                        <i class="bi bi-tools"></i> 管理指令测试
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="bi bi-activity"></i> 实时日志</h5>
            </div>
            <div class="card-body">
                <div id="test-logs" style="height: 200px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 5px;">
                    <p class="text-muted">等待测试消息...</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    const socket = io();
    
    // 连接成功
    socket.on('connect', function() {
        addLog('✅ WebSocket 连接成功', 'success');
    });
    
    // 接收测试消息发送事件
    socket.on('test_message_sent', function(data) {
        addLog(`📤 测试消息已发送: ${data.sender} -> ${data.content}`, 'info');
    });
    
    // 提交测试消息表单
    document.getElementById('test-message-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const testData = {
            group: document.getElementById('test-group').value,
            sender: document.getElementById('test-sender').value,
            content: document.getElementById('test-content').value
        };
        
        sendTestMessage(testData);
    });
    
    // 发送测试消息
    function sendTestMessage(data) {
        addLog(`🔄 发送测试消息: ${data.sender} -> ${data.group}`, 'info');
        
        fetch('/api/test/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                addLog(`✅ ${result.message}`, 'success');
                addTestResult('success', `消息发送成功: ${data.content}`);
            } else {
                addLog(`❌ ${result.message}`, 'danger');
                addTestResult('error', `消息发送失败: ${result.message}`);
            }
        })
        .catch(error => {
            addLog(`❌ 发送失败: ${error.message}`, 'danger');
            addTestResult('error', `发送失败: ${error.message}`);
        });
    }
    
    // 快速测试
    function quickTest(type) {
        const tests = {
            '普通问题': {
                group: '技术支持群',
                sender: '测试用户',
                content: '@小助手 如何安装设备？'
            },
            '禁答域问题': {
                group: '技术支持群',
                sender: '测试用户',
                content: '@小助手 你们的价格是多少？'
            },
            '管理指令': {
                group: '技术支持群',
                sender: '管理员',
                content: '@小助手 #status'
            }
        };
        
        const testData = tests[type];
        if (testData) {
            // 更新表单
            document.getElementById('test-group').value = testData.group;
            document.getElementById('test-sender').value = testData.sender;
            document.getElementById('test-content').value = testData.content;
            
            // 发送测试
            sendTestMessage(testData);
        }
    }
    
    // 添加日志
    function addLog(message, type = 'info') {
        const logsDiv = document.getElementById('test-logs');
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `mb-1 text-${type}`;
        logEntry.innerHTML = `<small>[${timestamp}]</small> ${message}`;
        
        logsDiv.appendChild(logEntry);
        logsDiv.scrollTop = logsDiv.scrollHeight;
        
        // 限制日志条数
        while (logsDiv.children.length > 50) {
            logsDiv.removeChild(logsDiv.firstChild);
        }
    }
    
    // 添加测试结果
    function addTestResult(type, message) {
        const resultsDiv = document.getElementById('test-results');
        const resultEntry = document.createElement('div');
        resultEntry.className = `alert alert-${type} alert-sm mb-2`;
        resultEntry.innerHTML = `
            <small><strong>[${new Date().toLocaleTimeString()}]</strong></small><br>
            ${message}
        `;
        
        resultsDiv.appendChild(resultEntry);
        
        // 限制结果条数
        while (resultsDiv.children.length > 10) {
            resultsDiv.removeChild(resultsDiv.firstChild);
        }
    }
</script>
{% endblock %}'''
    
    # 写入模板文件
    (templates_dir / 'base.html').write_text(base_template, encoding='utf-8')
    (templates_dir / 'index.html').write_text(index_template, encoding='utf-8')
    (templates_dir / 'config.html').write_text(config_template, encoding='utf-8')
    (templates_dir / 'monitor.html').write_text(monitor_template, encoding='utf-8')
    (templates_dir / 'logs.html').write_text(logs_template, encoding='utf-8')
    (templates_dir / 'test.html').write_text(test_template, encoding='utf-8')

def main():
    """主函数"""
    print("🚀 启动微信客服中台 Web 前端...")
    
    # 创建模板文件
    create_templates()
    
    # 加载配置
    load_config()
    
    print("📱 Web 界面已启动:")
    print("   主页: http://localhost:5000")
    print("   配置: http://localhost:5000/config")
    print("   监控: http://localhost:5000/monitor")
    print("   日志: http://localhost:5000/logs")
    print("   客户管理: http://localhost:5000/customers")
    print("   测试: http://localhost:5000/test")
    print()
    print("💡 使用说明:")
    print("   1. 访问配置页面设置 API 密钥")
    print("   2. 在客户管理页面注册和管理客户")
    print("   3. 在监控页面查看系统状态")
    print("   4. 在测试页面发送测试消息")
    print("   5. 在日志页面查看消息记录")
    print()
    print("按 Ctrl+C 停止服务器")
    
    # 启动服务器
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")

if __name__ == "__main__":
    main()
