#!/usr/bin/env python3
"""
完整的向量数据库测试流程
"""

import os
import sys
import asyncio
import logging
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def complete_vector_test():
    """完整的向量数据库测试"""
    try:
        from supabase import create_client, Client
        
        logger.info("🚀 开始完整的向量数据库测试...")
        
        # 1. 连接 Supabase
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        supabase: Client = create_client(url, key)
        
        logger.info("✅ Supabase 连接成功")
        
        # 2. 使用 Qwen 生成嵌入向量
        qwen_key = os.getenv("QWEN_API_KEY")
        
        test_documents = [
            "充电桩故障排除指南",
            "如何安装充电桩",
            "充电桩维护保养方法",
            "充电桩安全使用注意事项"
        ]
        
        embeddings = []
        
        for i, doc in enumerate(test_documents):
            logger.info(f"🔍 生成文档 {i+1} 的嵌入向量: {doc}")
            
            headers = {
                "Authorization": f"Bearer {qwen_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "text-embedding-v2",
                "input": {
                    "texts": [doc]
                }
            }
            
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result['output']['embeddings'][0]['embedding']
                embeddings.append({
                    'id': i + 1,
                    'content': doc,
                    'embedding': embedding,
                    'metadata': {
                        'title': doc,
                        'source': 'test_documents',
                        'created_at': '2025-10-27T23:30:00Z'
                    }
                })
                logger.info(f"✅ 文档 {i+1} 嵌入向量生成成功: 维度 {len(embedding)}")
            else:
                logger.error(f"❌ 文档 {i+1} 嵌入向量生成失败: {response.status_code}")
                return False
        
        # 3. 插入到数据库
        logger.info("📥 插入向量数据到数据库...")
        
        for embedding_data in embeddings:
            try:
                insert_result = supabase.table('embeddings').insert(embedding_data).execute()
                logger.info(f"✅ 文档 {embedding_data['id']} 插入成功")
            except Exception as e:
                logger.error(f"❌ 文档 {embedding_data['id']} 插入失败: {e}")
                return False
        
        # 4. 测试搜索
        logger.info("🔍 测试向量搜索...")
        
        # 搜索查询
        search_query = "充电桩坏了怎么办"
        
        # 生成查询向量
        headers = {
            "Authorization": f"Bearer {qwen_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "text-embedding-v2",
            "input": {
                "texts": [search_query]
            }
        }
        
        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            query_embedding = result['output']['embeddings'][0]['embedding']
            
            # 搜索相似文档
            search_result = supabase.rpc('search_embeddings', {
                'query_embedding': query_embedding,
                'match_count': 3
            }).execute()
            
            logger.info(f"✅ 搜索成功: 找到 {len(search_result.data)} 条结果")
            
            # 显示搜索结果
            logger.info("📋 搜索结果:")
            for i, item in enumerate(search_result.data):
                logger.info(f"   {i+1}. {item.get('content', 'N/A')}")
                logger.info(f"      相似度: {item.get('similarity', 'N/A'):.4f}")
                logger.info(f"      ID: {item.get('id', 'N/A')}")
        else:
            logger.error(f"❌ 查询向量生成失败: {response.status_code}")
            return False
        
        # 5. 清理测试数据
        logger.info("🧹 清理测试数据...")
        
        for embedding_data in embeddings:
            try:
                delete_result = supabase.table('embeddings').delete().eq('id', embedding_data['id']).execute()
                logger.info(f"✅ 文档 {embedding_data['id']} 清理完成")
            except Exception as e:
                logger.error(f"❌ 文档 {embedding_data['id']} 清理失败: {e}")
        
        logger.info("🎉 完整测试流程成功！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 完整测试失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("🚀 开始完整的向量数据库测试...")
    logger.info("=" * 60)
    
    success = await complete_vector_test()
    
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("🎉 向量数据库完全正常！可以开始使用了！")
        logger.info("💡 建议使用 Supabase Postgrestools 扩展管理数据库")
    else:
        logger.error("❌ 向量数据库测试失败，需要修复")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
