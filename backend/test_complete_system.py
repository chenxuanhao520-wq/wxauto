#!/usr/bin/env python3
"""
完整系统流程测试
测试从向量数据库到AI响应的完整流程
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteSystemTest:
    """完整系统测试"""
    
    def __init__(self):
        """初始化测试"""
        self.url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.url or not self.service_key:
            raise ValueError("缺少 Supabase 环境变量")
        
        from supabase import create_client, Client
        self.supabase: Client = create_client(self.url, self.service_key)
        
        logger.info("✅ 完整系统测试初始化成功")
    
    async def test_vector_database(self):
        """测试向量数据库"""
        try:
            logger.info("🔍 测试向量数据库...")
            
            # 测试 embeddings 表
            result = self.supabase.table('embeddings').select('*').limit(1).execute()
            logger.info(f"✅ embeddings 表正常: {len(result.data)} 条记录")
            
            # 测试向量搜索函数
            test_vector = [0.1] * 1536
            search_result = self.supabase.rpc('search_embeddings', {
                'query_embedding': test_vector,
                'match_count': 3
            }).execute()
            logger.info(f"✅ 向量搜索函数正常: {len(search_result.data)} 条结果")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 向量数据库测试失败: {e}")
            return False
    
    async def test_embedding_service(self):
        """测试嵌入服务"""
        try:
            logger.info("🔍 测试嵌入服务...")
            
            # 尝试导入嵌入服务
            try:
                from modules.embeddings.unified_embedding_service import get_embedding_service
                embedding_service = get_embedding_service()
                
                # 测试文本嵌入
                test_text = "充电桩故障排除指南"
                embedding = await embedding_service.embed_text(test_text)
                
                if embedding and len(embedding) == 1536:
                    logger.info(f"✅ 嵌入服务正常: 维度 {len(embedding)}")
                    return True
                else:
                    logger.warning(f"⚠️ 嵌入服务异常: 维度 {len(embedding) if embedding else 0}")
                    return False
                    
            except ImportError as e:
                logger.warning(f"⚠️ 嵌入服务模块未找到: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 嵌入服务测试失败: {e}")
            return False
    
    async def test_ai_gateway(self):
        """测试AI网关"""
        try:
            logger.info("🔍 测试AI网关...")
            
            # 尝试导入AI网关
            try:
                from modules.ai_gateway.gateway import AIGateway
                ai_gateway = AIGateway()
                
                # 测试AI响应
                test_message = "你好，我是测试用户"
                response = ai_gateway.generate(
                    user_message=test_message,
                    evidence_context="",
                    session_history=None,
                    max_tokens=100,
                    temperature=0.7
                )
                
                if response and response.content:
                    logger.info(f"✅ AI网关正常: {response.content[:50]}...")
                    return True
                else:
                    logger.warning("⚠️ AI网关响应异常")
                    return False
                    
            except ImportError as e:
                logger.warning(f"⚠️ AI网关模块未找到: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ AI网关测试失败: {e}")
            return False
    
    async def test_complete_flow(self):
        """测试完整流程"""
        try:
            logger.info("🔍 测试完整流程...")
            
            # 1. 测试向量数据库
            vector_ok = await self.test_vector_database()
            
            # 2. 测试嵌入服务
            embedding_ok = await self.test_embedding_service()
            
            # 3. 测试AI网关
            ai_ok = await self.test_ai_gateway()
            
            # 4. 模拟完整流程
            if vector_ok and embedding_ok and ai_ok:
                logger.info("🎯 模拟完整RAG流程...")
                
                # 模拟用户查询
                user_query = "充电桩无法启动怎么办？"
                logger.info(f"📝 用户查询: {user_query}")
                
                # 生成查询向量（模拟）
                query_vector = [0.2] * 1536
                
                # 向量搜索
                search_results = self.supabase.rpc('search_embeddings', {
                    'query_embedding': query_vector,
                    'match_count': 3
                }).execute()
                
                logger.info(f"🔍 找到 {len(search_results.data)} 条相关文档")
                
                # 构建上下文
                context = ""
                for i, result in enumerate(search_results.data):
                    context += f"文档{i+1}: {result.get('content', '')[:100]}...\n"
                
                logger.info(f"📚 构建上下文: {len(context)} 字符")
                
                # AI响应（模拟）
                logger.info("🤖 生成AI响应...")
                logger.info("✅ 完整流程测试成功！")
                
                return True
            else:
                logger.warning("⚠️ 部分组件测试失败，无法完成完整流程")
                return False
                
        except Exception as e:
            logger.error(f"❌ 完整流程测试失败: {e}")
            return False
    
    async def test_performance(self):
        """测试性能"""
        try:
            logger.info("🔍 测试系统性能...")
            
            import time
            
            # 测试向量搜索性能
            start_time = time.time()
            test_vector = [0.1] * 1536
            search_result = self.supabase.rpc('search_embeddings', {
                'query_embedding': test_vector,
                'match_count': 5
            }).execute()
            search_time = time.time() - start_time
            
            logger.info(f"⚡ 向量搜索性能: {search_time:.3f}秒")
            
            # 测试数据库连接性能
            start_time = time.time()
            result = self.supabase.table('embeddings').select('*').limit(1).execute()
            db_time = time.time() - start_time
            
            logger.info(f"⚡ 数据库连接性能: {db_time:.3f}秒")
            
            # 性能评估
            if search_time < 1.0 and db_time < 0.5:
                logger.info("✅ 性能测试通过")
                return True
            else:
                logger.warning("⚠️ 性能需要优化")
                return False
                
        except Exception as e:
            logger.error(f"❌ 性能测试失败: {e}")
            return False

async def main():
    """主函数"""
    logger.info("🚀 完整系统流程测试...")
    logger.info("=" * 60)
    
    try:
        # 初始化测试
        tester = CompleteSystemTest()
        
        # 测试各个组件
        logger.info("\n🧪 测试各个组件...")
        vector_ok = await tester.test_vector_database()
        embedding_ok = await tester.test_embedding_service()
        ai_ok = await tester.test_ai_gateway()
        
        # 测试完整流程
        logger.info("\n🎯 测试完整流程...")
        flow_ok = await tester.test_complete_flow()
        
        # 测试性能
        logger.info("\n⚡ 测试性能...")
        perf_ok = await tester.test_performance()
        
        # 输出总结
        logger.info("\n" + "=" * 60)
        logger.info("📊 系统测试结果:")
        logger.info("=" * 60)
        
        logger.info(f"向量数据库: {'✅ 正常' if vector_ok else '❌ 异常'}")
        logger.info(f"嵌入服务: {'✅ 正常' if embedding_ok else '❌ 异常'}")
        logger.info(f"AI网关: {'✅ 正常' if ai_ok else '❌ 异常'}")
        logger.info(f"完整流程: {'✅ 正常' if flow_ok else '❌ 异常'}")
        logger.info(f"系统性能: {'✅ 正常' if perf_ok else '❌ 异常'}")
        
        # 总体评估
        all_ok = vector_ok and embedding_ok and ai_ok and flow_ok and perf_ok
        
        if all_ok:
            logger.info("\n🎉 系统测试全部通过！")
            logger.info("💡 系统已准备好投入使用")
        else:
            logger.info("\n⚠️ 部分测试未通过")
            logger.info("💡 需要进一步优化")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 系统测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
