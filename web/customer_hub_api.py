"""
客户中台 REST API
提供未知池、建档升级、状态操作、触发等接口
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Dict, Any

# 添加项目路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'modules'))

from modules.customer_hub.service import CustomerHubService
from modules.customer_hub.types import InboundMessage, Party

logger = logging.getLogger(__name__)

# 创建Blueprint
customer_hub_bp = Blueprint('customer_hub', __name__, url_prefix='/api/hub')

# 服务实例
hub_service = CustomerHubService()


# ==================== 辅助函数 ====================

def success_response(data: Any = None, message: str = "success") -> Dict:
    """成功响应"""
    return {
        'success': True,
        'message': message,
        'data': data
    }


def error_response(message: str, code: int = 400, data: Any = None) -> tuple:
    """错误响应"""
    return {
        'success': False,
        'message': message,
        'data': data
    }, code


# ==================== 未知池 ====================

@customer_hub_bp.route('/unknown-pool', methods=['GET'])
def get_unknown_pool():
    """
    获取未知池(灰名单且未处理的会话)
    
    Query Params:
        limit: 最大数量,默认100
    
    Returns:
        会话列表
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        
        pool = hub_service.get_unknown_pool(limit)
        
        return jsonify(success_response(pool))
    
    except Exception as e:
        logger.error(f"获取未知池失败: {e}", exc_info=True)
        return jsonify(error_response(str(e)))


@customer_hub_bp.route('/today-todo', methods=['GET'])
def get_today_todo():
    """
    获取今日待办
    
    Query Params:
        limit: 最大数量,默认100
    
    Returns:
        会话列表
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        
        todo = hub_service.get_today_todo(limit)
        
        return jsonify(success_response(todo))
    
    except Exception as e:
        logger.error(f"获取今日待办失败: {e}", exc_info=True)
        return jsonify(error_response(str(e)))


# ==================== 统计 ====================

@customer_hub_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    获取统计信息
    
    Returns:
        统计数据
    """
    try:
        stats = hub_service.get_statistics()
        
        return jsonify(success_response(stats))
    
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        return jsonify(error_response(str(e)))


# ==================== 建档与升级 ====================

@customer_hub_bp.route('/contacts/promote', methods=['POST'])
def promote_to_customer():
    """
    建档+编码(升白)
    
    Request Body:
        contact_id: 联系人ID
        customer_name: 客户名称
        region: 地区代码(可选)
        level: 客户级别(可选)
        owner: 负责人(可选)
    
    Returns:
        更新后的联系人信息
    """
    try:
        data = request.get_json()
        
        contact_id = data.get('contact_id')
        customer_name = data.get('customer_name')
        region = data.get('region')
        level = data.get('level')
        owner = data.get('owner')
        
        if not contact_id or not customer_name:
            return jsonify(error_response('缺少必要参数: contact_id, customer_name'))
        
        result = hub_service.promote_to_customer(
            contact_id=contact_id,
            customer_name=customer_name,
            region=region,
            level=level,
            owner=owner
        )
        
        return jsonify(success_response(result, '建档成功'))
    
    except Exception as e:
        logger.error(f"建档失败: {e}", exc_info=True)
        return jsonify(error_response(str(e)))


# ==================== 状态操作 ====================

@customer_hub_bp.route('/threads/<thread_id>/snooze', methods=['POST'])
def snooze_thread(thread_id: str):
    """
    推迟处理(Snooze)
    
    Request Body:
        snooze_minutes: 推迟时长(分钟),默认60
    
    Returns:
        操作结果
    """
    try:
        data = request.get_json() or {}
        snooze_minutes = data.get('snooze_minutes', 60)
        
        result = hub_service.snooze_thread(thread_id, snooze_minutes)
        
        return jsonify(success_response(result, '已推迟处理'))
    
    except ValueError as e:
        return jsonify(error_response(str(e), 404))
    except Exception as e:
        logger.error(f"推迟处理失败: {e}", exc_info=True)
        return jsonify(error_response(str(e)))


@customer_hub_bp.route('/threads/<thread_id>/resolve', methods=['POST'])
def resolve_thread(thread_id: str):
    """
    标记为已解决
    
    Returns:
        操作结果
    """
    try:
        result = hub_service.resolve_thread(thread_id)
        
        return jsonify(success_response(result, '已标记为已解决'))
    
    except ValueError as e:
        return jsonify(error_response(str(e), 404))
    except Exception as e:
        logger.error(f"标记已解决失败: {e}", exc_info=True)
        return jsonify(error_response(str(e)))


@customer_hub_bp.route('/threads/<thread_id>/waiting', methods=['POST'])
def mark_waiting(thread_id: str):
    """
    标记为等待对方
    
    Request Body:
        follow_up_hours: 跟进小时数(可选)
    
    Returns:
        操作结果
    """
    try:
        data = request.get_json() or {}
        follow_up_hours = data.get('follow_up_hours')
        
        result = hub_service.mark_waiting(thread_id, follow_up_hours)
        
        return jsonify(success_response(result, '已标记为等待对方'))
    
    except ValueError as e:
        return jsonify(error_response(str(e), 404))
    except Exception as e:
        logger.error(f"标记等待对方失败: {e}", exc_info=True)
        return jsonify(error_response(str(e)))


@customer_hub_bp.route('/threads/<thread_id>/recalc', methods=['POST'])
def recalc_thread_status(thread_id: str):
    """
    重新计算线程状态
    
    Returns:
        操作结果
    """
    try:
        result = hub_service.recalc_thread_status(thread_id)
        
        return jsonify(success_response(result, '状态已重算'))
    
    except ValueError as e:
        return jsonify(error_response(str(e), 404))
    except Exception as e:
        logger.error(f"重算状态失败: {e}", exc_info=True)
        return jsonify(error_response(str(e)))


# ==================== 触发器 ====================

@customer_hub_bp.route('/threads/<thread_id>/trigger', methods=['POST'])
async def trigger_scenario(thread_id: str):
    """
    触发LLM场景(售前/售后/客户开发)
    
    Request Body:
        text: 对话文本
        trigger_type: 触发类型 ('售前'|'售后'|'客户开发')
    
    Returns:
        触发输出(表单+回复草稿)
    """
    try:
        data = request.get_json()
        
        text = data.get('text')
        trigger_type = data.get('trigger_type')
        
        if not text or not trigger_type:
            return jsonify(error_response('缺少必要参数: text, trigger_type'))
        
        if trigger_type not in ['售前', '售后', '客户开发']:
            return jsonify(error_response('无效的触发类型,必须是: 售前/售后/客户开发'))
        
        result = await hub_service.trigger_scenario(
            thread_id=thread_id,
            text=text,
            trigger_type=trigger_type
        )
        
        if 'error' in result:
            return jsonify(error_response(result['message']))
        
        return jsonify(success_response(result, '触发成功'))
    
    except ValueError as e:
        return jsonify(error_response(str(e), 404))
    except Exception as e:
        logger.error(f"触发失败: {e}", exc_info=True)
        return jsonify(error_response(str(e)))


# ==================== 消息处理 ====================

@customer_hub_bp.route('/messages/process', methods=['POST'])
def process_message():
    """
    处理入站消息
    
    Request Body:
        wx_id: 微信ID
        thread_id: 会话ID(可选)
        text: 消息文本(可选)
        file_types: 文件类型列表(可选)
        last_speaker: 最后说话方 ('me'|'them')
        timestamp: 时间戳(可选,默认当前时间)
        kb_matched: 是否匹配到知识库(可选,默认false)
    
    Returns:
        处理结果
    """
    try:
        data = request.get_json()
        
        wx_id = data.get('wx_id')
        thread_id = data.get('thread_id', '')
        text = data.get('text')
        file_types = data.get('file_types', [])
        last_speaker = data.get('last_speaker')
        timestamp_str = data.get('timestamp')
        kb_matched = data.get('kb_matched', False)
        
        if not wx_id or not last_speaker:
            return jsonify(error_response('缺少必要参数: wx_id, last_speaker'))
        
        # 解析时间戳
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.now()
        
        # 解析last_speaker
        try:
            speaker = Party(last_speaker)
        except ValueError:
            return jsonify(error_response('无效的last_speaker,必须是: me 或 them'))
        
        # 构建消息对象
        message = InboundMessage(
            wx_id=wx_id,
            thread_id=thread_id,
            text=text,
            file_types=file_types,
            timestamp=timestamp,
            last_speaker=speaker
        )
        
        # 处理消息
        result = hub_service.process_inbound_message(message, kb_matched)
        
        return jsonify(success_response(result, '消息处理完成'))
    
    except Exception as e:
        logger.error(f"处理消息失败: {e}", exc_info=True)
        return jsonify(error_response(str(e)))


# ==================== 定时任务 ====================

@customer_hub_bp.route('/cron/recalc', methods=['POST'])
def cron_recalc_all():
    """
    定时任务: 重新计算所有线程状态
    
    Returns:
        统计结果
    """
    try:
        result = hub_service.recalc_all_threads()
        
        return jsonify(success_response(result, '所有线程状态已重算'))
    
    except Exception as e:
        logger.error(f"定时重算失败: {e}", exc_info=True)
        return jsonify(error_response(str(e)))


# ==================== 健康检查 ====================

@customer_hub_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'customer_hub',
        'timestamp': datetime.now().isoformat()
    })


# ==================== 导出函数 ====================

def register_customer_hub_api(app):
    """
    注册客户中台API到Flask应用
    
    Args:
        app: Flask应用实例
    """
    app.register_blueprint(customer_hub_bp)
    logger.info("客户中台API已注册")

