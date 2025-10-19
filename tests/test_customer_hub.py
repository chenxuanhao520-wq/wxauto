#!/usr/bin/env python3
"""
客户中台测试用例
包含seed数据和验收测试
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from modules.customer_hub.types import (
    InboundMessage, Party, Contact, Thread,
    ContactType, ContactSource, ThreadStatus, Bucket
)
from modules.customer_hub.service import CustomerHubService
from modules.customer_hub.repository import CustomerHubRepository
from modules.customer_hub.state_machine import StateMachine, SLAConfig
from modules.customer_hub.scoring import ScoringEngine


# ==================== 测试数据 ====================

# 样例测试事件(来自需求文档)
SAMPLE_EVENTS = [
    {
        "wx_id": "wx_u_001",
        "thread_id": "t001",
        "text": "你好，发下320kW双枪报价和交期，含税，发票要专票。",
        "file_types": ["pdf"],
        "ts": "2025-10-18T09:10:00Z",
        "last_speaker": "them"
    },
    {
        "wx_id": "wx_u_002",
        "thread_id": "t002",
        "text": "设备报警码E103，无法充电，已重启无效，求远程支持。",
        "file_types": [],
        "ts": "2025-10-18T10:05:00Z",
        "last_speaker": "them"
    },
    {
        "wx_id": "wx_u_003",
        "thread_id": "t003",
        "text": "想聊代理和样板合作，返利政策怎么定？",
        "file_types": ["docx"],
        "ts": "2025-10-18T03:12:00Z",
        "last_speaker": "them"
    },
    {
        "wx_id": "wx_friend",
        "thread_id": "t004",
        "text": "晚上撸串？",
        "file_types": [],
        "ts": "2025-10-18T12:30:00Z",
        "last_speaker": "them"
    }
]


# ==================== 测试类 ====================

class CustomerHubTester:
    """客户中台测试器"""
    
    def __init__(self):
        self.service = CustomerHubService()
        self.repo = CustomerHubRepository()
        print("✅ 测试器初始化完成")
    
    def setup_database(self):
        """初始化数据库"""
        print("\n📦 初始化数据库...")
        
        # 执行升级脚本
        sql_file = Path(__file__).parent / "sql" / "upgrade_customer_hub.sql"
        
        if not sql_file.exists():
            print("❌ 升级脚本不存在:", sql_file)
            return False
        
        conn = self.repo.connect()
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        try:
            conn.executescript(sql_script)
            conn.commit()
            print("✅ 数据库表结构初始化成功")
            return True
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False
    
    def seed_sample_events(self):
        """导入样例测试事件"""
        print("\n🌱 导入样例测试事件...")
        
        results = []
        
        for event in SAMPLE_EVENTS:
            # 解析时间戳
            timestamp = datetime.fromisoformat(event['ts'].replace('Z', '+00:00'))
            
            # 构建消息对象
            message = InboundMessage(
                wx_id=event['wx_id'],
                thread_id=event['thread_id'],
                text=event['text'],
                file_types=event['file_types'],
                timestamp=timestamp,
                last_speaker=Party(event['last_speaker'])
            )
            
            # 处理消息
            result = self.service.process_inbound_message(message, kb_matched=False)
            
            results.append({
                'wx_id': event['wx_id'],
                'bucket': result['bucket'],
                'score': result['total_score'],
                'trigger_type': result.get('trigger_type'),
                'status': result['status']
            })
            
            print(f"  ✓ {event['wx_id'][:10]}: "
                  f"bucket={result['bucket']}, "
                  f"score={result['total_score']}, "
                  f"trigger={result.get('trigger_type') or 'None'}")
        
        print(f"\n✅ 成功导入 {len(results)} 条样例事件")
        return results
    
    def verify_acceptance_criteria(self, results):
        """验收标准检查"""
        print("\n✅ 验收标准检查...")
        
        # 1. t001 命中"售前"、进入 GRAY 或 WHITE
        t001 = next((r for r in results if r['wx_id'] == 'wx_u_001'), None)
        if t001:
            assert t001['trigger_type'] == '售前', f"t001 应命中售前,实际: {t001['trigger_type']}"
            assert t001['bucket'] in ['GRAY', 'WHITE'], f"t001 应进入 GRAY/WHITE,实际: {t001['bucket']}"
            print("  ✓ t001 命中售前 ✅")
        
        # 2. t002 命中"售后"、进入 GRAY 或 WHITE
        t002 = next((r for r in results if r['wx_id'] == 'wx_u_002'), None)
        if t002:
            assert t002['trigger_type'] == '售后', f"t002 应命中售后,实际: {t002['trigger_type']}"
            assert t002['bucket'] in ['GRAY', 'WHITE'], f"t002 应进入 GRAY/WHITE,实际: {t002['bucket']}"
            print("  ✓ t002 命中售后 ✅")
        
        # 3. t003 命中"客户开发"、进入 GRAY 或 WHITE
        t003 = next((r for r in results if r['wx_id'] == 'wx_u_003'), None)
        if t003:
            assert t003['trigger_type'] == '客户开发', f"t003 应命中客户开发,实际: {t003['trigger_type']}"
            assert t003['bucket'] in ['GRAY', 'WHITE'], f"t003 应进入 GRAY/WHITE,实际: {t003['bucket']}"
            print("  ✓ t003 命中客户开发 ✅")
        
        # 4. t004 → BLACK，不入队
        t004 = next((r for r in results if r['wx_id'] == 'wx_friend'), None)
        if t004:
            assert t004['bucket'] == 'BLACK', f"t004 应进入 BLACK,实际: {t004['bucket']}"
            assert t004['trigger_type'] is None, f"t004 不应触发,实际: {t004['trigger_type']}"
            print("  ✓ t004 进入黑名单,不触发 ✅")
        
        print("\n✅ 所有验收标准通过!")
    
    def test_state_machine(self):
        """测试状态机"""
        print("\n🔄 测试状态机...")
        
        sm = StateMachine(SLAConfig(
            need_reply_minutes=30,
            follow_up_hours=48
        ))
        
        # 测试1: 客户最后发言,未超时 -> NEED_REPLY
        now = datetime.now()
        thread = Thread(
            id="test_thread_1",
            contact_id="test_contact_1",
            last_speaker=Party.THEM,
            last_msg_at=now - timedelta(minutes=10),  # 10分钟前
            status=ThreadStatus.UNSEEN,
            bucket=Bucket.GRAY
        )
        
        status = sm.compute_status(thread, now)
        assert status == ThreadStatus.NEED_REPLY, f"期望 NEED_REPLY,实际: {status}"
        print("  ✓ 客户发言未超时 -> NEED_REPLY ✅")
        
        # 测试2: 客户最后发言,已超时 -> OVERDUE
        thread.last_msg_at = now - timedelta(minutes=40)  # 40分钟前
        status = sm.compute_status(thread, now)
        assert status == ThreadStatus.OVERDUE, f"期望 OVERDUE,实际: {status}"
        print("  ✓ 客户发言超时 -> OVERDUE ✅")
        
        # 测试3: 我方最后发言,未超时 -> WAITING_THEM
        thread.last_speaker = Party.ME
        thread.last_msg_at = now - timedelta(hours=24)  # 24小时前
        status = sm.compute_status(thread, now)
        assert status == ThreadStatus.WAITING_THEM, f"期望 WAITING_THEM,实际: {status}"
        print("  ✓ 我方发言未超时 -> WAITING_THEM ✅")
        
        # 测试4: 我方最后发言,已超时 -> NEED_REPLY(回弹)
        thread.last_msg_at = now - timedelta(hours=50)  # 50小时前
        status = sm.compute_status(thread, now)
        assert status == ThreadStatus.NEED_REPLY, f"期望 NEED_REPLY(回弹),实际: {status}"
        print("  ✓ 我方发言超时 -> NEED_REPLY(回弹) ✅")
        
        print("\n✅ 状态机测试通过!")
    
    def test_scoring_engine(self):
        """测试打分引擎"""
        print("\n⚖️ 测试打分引擎...")
        
        se = ScoringEngine()
        
        # 测试1: 售前关键词
        signal, details = se.score_message(
            text="请问320kW充电桩报价多少？需要含税发票",
            file_types=["pdf"],
            timestamp=datetime(2025, 10, 18, 9, 30),  # 工作日工作时间
            kb_matched=True
        )
        
        print(f"  售前消息: score={signal.total_score}, bucket={signal.bucket.value}")
        assert signal.total_score >= 60, "售前消息应该>=60分"
        assert signal.bucket in [Bucket.GRAY, Bucket.WHITE], "售前消息应进入灰/白名单"
        print("  ✓ 售前消息打分正确 ✅")
        
        # 测试2: 售后关键词
        signal, details = se.score_message(
            text="设备故障报警码E103无法充电，需要上门维修",
            file_types=[],
            timestamp=datetime(2025, 10, 18, 14, 0),
            kb_matched=False
        )
        
        print(f"  售后消息: score={signal.total_score}, bucket={signal.bucket.value}")
        assert signal.total_score >= 60, "售后消息应该>=60分"
        print("  ✓ 售后消息打分正确 ✅")
        
        # 测试3: 黑名单关键词
        signal, details = se.score_message(
            text="晚上一起吃饭打球？",
            file_types=[],
            timestamp=datetime(2025, 10, 18, 12, 0),
            kb_matched=False
        )
        
        print(f"  黑名单消息: score={signal.total_score}, bucket={signal.bucket.value}")
        assert signal.bucket == Bucket.BLACK, "黑名单关键词应进入黑名单"
        print("  ✓ 黑名单识别正确 ✅")
        
        # 测试4: 触发类型识别
        signal, _ = se.score_message(
            text="想了解代理政策和返点机制",
            file_types=["docx"],
            timestamp=datetime(2025, 10, 18, 10, 0),
            kb_matched=False
        )
        
        trigger_type = se.identify_trigger_type(signal.keyword_hits)
        print(f"  客户开发消息: trigger_type={trigger_type}")
        assert trigger_type == '客户开发', f"应识别为客户开发,实际: {trigger_type}"
        print("  ✓ 触发类型识别正确 ✅")
        
        print("\n✅ 打分引擎测试通过!")
    
    async def test_triggers(self):
        """测试触发器"""
        print("\n🚀 测试触发器...")
        
        from modules.customer_hub.triggers import TriggerEngine
        
        te = TriggerEngine()  # 使用模拟输出
        
        # 测试1: 售前触发
        output = await te.trigger_pre_sales(
            "你好，发下320kW双枪报价和交期，含税，发票要专票。"
        )
        
        assert '功率_kW' in output.form, "售前表单应包含功率字段"
        assert len(output.reply_draft) > 0, "应生成回复草稿"
        print(f"  ✓ 售前触发: {len(output.form)} 个字段, 草稿 {len(output.reply_draft)} 字 ✅")
        
        # 测试2: 售后触发
        output = await te.trigger_after_sales(
            "设备报警码E103，无法充电，已重启无效，求远程支持。"
        )
        
        assert '报警码' in output.form, "售后表单应包含报警码字段"
        print(f"  ✓ 售后触发: {len(output.form)} 个字段, 草稿 {len(output.reply_draft)} 字 ✅")
        
        # 测试3: 客户开发触发
        output = await te.trigger_bizdev(
            "想聊代理和样板合作，返利政策怎么定？"
        )
        
        assert '线索级别' in output.form, "客户开发表单应包含线索级别字段"
        print(f"  ✓ 客户开发触发: {len(output.form)} 个字段, 草稿 {len(output.reply_draft)} 字 ✅")
        
        print("\n✅ 触发器测试通过!")
    
    def test_unknown_pool(self):
        """测试未知池查询"""
        print("\n📥 测试未知池查询...")
        
        pool = self.service.get_unknown_pool(limit=100)
        
        print(f"  未知池数量: {len(pool)}")
        
        if len(pool) > 0:
            item = pool[0]
            print(f"  第一项: wx_id={item['wx_id']}, score={item['total_score']}")
        
        print("  ✓ 未知池查询成功 ✅")
    
    def test_today_todo(self):
        """测试今日待办查询"""
        print("\n📋 测试今日待办查询...")
        
        todo = self.service.get_today_todo(limit=100)
        
        print(f"  今日待办数量: {len(todo)}")
        
        if len(todo) > 0:
            item = todo[0]
            print(f"  第一项: status={item['status']}, bucket={item['bucket']}")
        
        print("  ✓ 今日待办查询成功 ✅")
    
    def test_statistics(self):
        """测试统计查询"""
        print("\n📊 测试统计查询...")
        
        stats = self.service.get_statistics()
        
        print(f"  统计数据: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        print("  ✓ 统计查询成功 ✅")
    
    def test_promote_customer(self):
        """测试建档升级"""
        print("\n⬆️ 测试建档升级...")
        
        # 找一个灰名单联系人
        pool = self.service.get_unknown_pool(limit=1)
        
        if len(pool) == 0:
            print("  ⚠️ 未知池为空,跳过建档测试")
            return
        
        item = pool[0]
        contact_id = item['contact_id']
        
        # 建档
        result = self.service.promote_to_customer(
            contact_id=contact_id,
            customer_name="张三",
            region="渝A",
            level="VIP",
            owner="销售A"
        )
        
        print(f"  ✓ 建档成功: K编码={result['k_code']}, 置信度={result['confidence']} ✅")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🧪 客户中台测试套件")
        print("=" * 60)
        
        # 1. 初始化数据库
        if not self.setup_database():
            print("\n❌ 数据库初始化失败,终止测试")
            return False
        
        # 2. 单元测试
        try:
            self.test_state_machine()
            self.test_scoring_engine()
            asyncio.run(self.test_triggers())
        except AssertionError as e:
            print(f"\n❌ 单元测试失败: {e}")
            return False
        
        # 3. 集成测试
        try:
            results = self.seed_sample_events()
            self.verify_acceptance_criteria(results)
        except AssertionError as e:
            print(f"\n❌ 集成测试失败: {e}")
            return False
        
        # 4. API测试
        try:
            self.test_unknown_pool()
            self.test_today_todo()
            self.test_statistics()
            # self.test_promote_customer()  # 可选,会修改数据
        except Exception as e:
            print(f"\n❌ API测试失败: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        
        return True


# ==================== 主函数 ====================

def main():
    """主函数"""
    tester = CustomerHubTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 客户中台系统验收通过!")
        print("\n📝 下一步:")
        print("  1. 访问 http://localhost:5000/customer-hub.html 查看前端界面")
        print("  2. 使用 POST /api/hub/messages/process 接入真实消息")
        print("  3. 配置 LLM 客户端启用智能触发")
        print("  4. 设置定时任务: POST /api/hub/cron/recalc 每小时重算状态")
    else:
        print("\n❌ 测试失败,请检查上述错误信息")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

