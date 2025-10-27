#!/usr/bin/env python3
"""
Supabase pgvector 向量数据库管理脚本
用于管理Supabase内置的pgvector向量数据库
"""

import asyncio
import logging
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入向量客户端
try:
    from backend.modules.vector.supabase_vector_client import SupabaseVectorClient
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录运行此脚本")
    exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorManagementTool:
    """Supabase pgvector 向量数据库管理工具"""
    
    def __init__(self):
        # Supabase配置
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # 向量配置
        self.table_name = os.getenv("VECTOR_TABLE_NAME", "knowledge_vectors")
        self.dimension = int(os.getenv("VECTOR_DIMENSION", "1536"))
        self.similarity_threshold = float(os.getenv("VECTOR_SIMILARITY_THRESHOLD", "0.7"))
        
        # 初始化客户端
        self.vector_client = None
        
    def init_client(self):
        """初始化向量数据库客户端"""
        try:
            if self.supabase_url and self.supabase_key:
                self.vector_client = SupabaseVectorClient(
                    self.supabase_url, 
                    self.supabase_key
                )
                logger.info("✅ Supabase向量客户端初始化成功")
                return True
            else:
                logger.error("❌ Supabase配置缺失")
                return False
                
        except Exception as e:
            logger.error(f"❌ 客户端初始化失败: {e}")
            return False
    
    async def test_connection(self):
        """测试连接"""
        if not self.vector_client:
            logger.error("❌ 客户端未初始化")
            return False
        
        try:
            logger.info("🔍 测试Supabase pgvector连接...")
            
            # 健康检查
            is_healthy = await self.vector_client.health_check()
            if is_healthy:
                logger.info("✅ 连接测试成功")
                return True
            else:
                logger.error("❌ 连接测试失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 连接测试失败: {e}")
            return False
    
    async def get_stats(self):
        """获取统计信息"""
        if not self.vector_client:
            logger.error("❌ 客户端未初始化")
            return
        
        try:
            stats = await self.vector_client.get_stats()
            logger.info(f"📊 向量数据库统计:")
            logger.info(f"   - 总向量数: {stats.get('total_vectors', 0)}")
            logger.info(f"   - 表名: {stats.get('table_name', 'N/A')}")
            logger.info(f"   - 最新更新: {stats.get('latest_update', 'N/A')}")
            
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
    
    async def test_search(self):
        """测试搜索功能"""
        if not self.vector_client:
            logger.error("❌ 客户端未初始化")
            return
        
        try:
            logger.info("🔍 测试向量搜索功能...")
            
            # 创建测试向量
            test_embedding = [0.1] * self.dimension
            
            # 执行搜索
            results = await self.vector_client.search_vectors(
                test_embedding, 
                top_k=5,
                similarity_threshold=self.similarity_threshold
            )
            
            logger.info(f"✅ 搜索测试完成，找到 {len(results)} 个结果")
            
            for i, result in enumerate(results[:3]):  # 只显示前3个
                logger.info(f"   {i+1}. ID: {result.get('id', 'N/A')}")
                logger.info(f"      相似度: {result.get('similarity', 0):.3f}")
                logger.info(f"      内容: {result.get('content', 'N/A')[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ 搜索测试失败: {e}")
    
    async def add_sample_data(self):
        """添加示例数据"""
        if not self.vector_client:
            logger.error("❌ 客户端未初始化")
            return
        
        try:
            logger.info("📝 添加示例数据...")
            
            # 示例向量数据
            sample_vectors = [
                {
                    "id": "sample_1",
                    "content": "充电桩故障排除指南",
                    "embedding": [0.1] * self.dimension,
                    "metadata": {"category": "troubleshooting", "type": "guide"}
                },
                {
                    "id": "sample_2", 
                    "content": "充电桩安装注意事项",
                    "embedding": [0.2] * self.dimension,
                    "metadata": {"category": "installation", "type": "manual"}
                },
                {
                    "id": "sample_3",
                    "content": "充电桩维护保养",
                    "embedding": [0.3] * self.dimension,
                    "metadata": {"category": "maintenance", "type": "guide"}
                }
            ]
            
            success = await self.vector_client.upsert_vectors(sample_vectors)
            if success:
                logger.info(f"✅ 成功添加 {len(sample_vectors)} 个示例向量")
            else:
                logger.error("❌ 添加示例数据失败")
                
        except Exception as e:
            logger.error(f"❌ 添加示例数据失败: {e}")
    
    async def cleanup_sample_data(self):
        """清理示例数据"""
        if not self.vector_client:
            logger.error("❌ 客户端未初始化")
            return
        
        try:
            logger.info("🗑️ 清理示例数据...")
            
            sample_ids = ["sample_1", "sample_2", "sample_3"]
            success = await self.vector_client.delete_vectors(sample_ids)
            
            if success:
                logger.info(f"✅ 成功删除 {len(sample_ids)} 个示例向量")
            else:
                logger.error("❌ 清理示例数据失败")
                
        except Exception as e:
            logger.error(f"❌ 清理示例数据失败: {e}")


async def main():
    """主函数"""
    print("🚀 Supabase pgvector 向量数据库管理工具")
    print("=" * 50)
    
    # 初始化管理工具
    management_tool = VectorManagementTool()
    
    if not management_tool.init_client():
        print("❌ 初始化失败，请检查配置")
        return
    
    # 显示菜单
    while True:
        print("\n📋 选择操作:")
        print("1. 测试连接")
        print("2. 查看统计信息")
        print("3. 测试搜索功能")
        print("4. 添加示例数据")
        print("5. 清理示例数据")
        print("6. 退出")
        
        choice = input("\n请输入选择 (1-6): ").strip()
        
        if choice == "1":
            print("\n🔍 测试连接...")
            success = await management_tool.test_connection()
            if success:
                print("✅ 连接测试成功！")
            else:
                print("❌ 连接测试失败！")
        
        elif choice == "2":
            print("\n📊 获取统计信息...")
            await management_tool.get_stats()
        
        elif choice == "3":
            print("\n🔍 测试搜索功能...")
            await management_tool.test_search()
        
        elif choice == "4":
            print("\n📝 添加示例数据...")
            await management_tool.add_sample_data()
        
        elif choice == "5":
            confirm = input("⚠️ 确认删除示例数据？(yes/no): ").strip().lower()
            if confirm == "yes":
                await management_tool.cleanup_sample_data()
            else:
                print("❌ 取消操作")
        
        elif choice == "6":
            print("👋 再见！")
            break
        
        else:
            print("❌ 无效选择，请重试")


if __name__ == "__main__":
    asyncio.run(main())
