#!/usr/bin/env python3
"""
知识库管理工具
用于添加、导入、导出知识库内容
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rag.retriever import Retriever
from storage.db import Database


def add_sample_documents(retriever: Retriever):
    """添加示例文档到知识库"""
    print("=" * 60)
    print("添加示例文档")
    print("=" * 60)
    
    # 示例文档1：产品安装指南
    install_chunks = [
        {
            'section': '第1章 安装前准备',
            'content': '设备安装前请确认：① 电源符合 220V±10% 要求；② 环境温度 0-40℃；③ 通风良好无尘。',
            'keywords': ['安装', '准备', '电源', '环境', '温度']
        },
        {
            'section': '第2章 安装步骤',
            'content': '安装步骤：① 关闭电源；② 固定底座（使用M6螺丝）；③ 连接电源线；④ 通电测试。注意：禁止带电操作。',
            'keywords': ['安装', '步骤', '固定', '连接', '测试', '螺丝']
        },
        {
            'section': '第3章 安装验证',
            'content': '安装完成后验证：① 指示灯正常闪烁；② 无异常声音；③ 温度正常（<45℃）。如有异常请立即断电并联系售后。',
            'keywords': ['验证', '指示灯', '温度', '异常', '售后']
        }
    ]
    
    retriever.add_document(
        document_name='产品安装指南',
        document_version='v2.1',
        chunks=install_chunks
    )
    
    # 示例文档2：故障排查手册
    troubleshoot_chunks = [
        {
            'section': '常见问题1：设备无法启动',
            'content': '设备无法启动排查：① 检查电源线是否连接；② 检查保险丝是否熔断；③ 检查开关是否打开。仍无法解决请联系技术支持。',
            'keywords': ['故障', '无法启动', '电源', '保险丝', '开关']
        },
        {
            'section': '常见问题2：设备过热',
            'content': '设备过热处理：① 立即断电；② 检查通风口是否堵塞；③ 等待冷却后再启动。长期过热可能损坏设备。',
            'keywords': ['故障', '过热', '断电', '通风', '冷却']
        },
        {
            'section': '常见问题3：指示灯异常',
            'content': '指示灯异常说明：红灯常亮=过热保护；黄灯闪烁=通信故障；绿灯不亮=电源异常。请根据指示灯状态排查。',
            'keywords': ['故障', '指示灯', '红灯', '黄灯', '绿灯', '异常']
        }
    ]
    
    retriever.add_document(
        document_name='故障排查手册',
        document_version='v1.5',
        chunks=troubleshoot_chunks
    )
    
    # 示例文档3：维护保养指南
    maintenance_chunks = [
        {
            'section': '日常维护',
            'content': '日常维护要点：① 每周清理灰尘；② 每月检查连接线；③ 每季度润滑活动部件。定期维护可延长使用寿命。',
            'keywords': ['维护', '保养', '清理', '检查', '润滑']
        },
        {
            'section': '年度保养',
            'content': '年度保养服务：① 全面清洁；② 更换易损件；③ 性能测试。建议联系官方服务中心进行专业保养。',
            'keywords': ['保养', '年度', '清洁', '更换', '测试', '服务']
        }
    ]
    
    retriever.add_document(
        document_name='维护保养指南',
        document_version='v1.0',
        chunks=maintenance_chunks
    )
    
    print(f"\n✅ 已添加 3 份文档，共 {len(install_chunks) + len(troubleshoot_chunks) + len(maintenance_chunks)} 个知识块")


def save_to_database(retriever: Retriever, db_path: str):
    """保存知识库到数据库"""
    print(f"\n保存知识库到数据库: {db_path}")
    retriever.save_to_db(db_path)
    print("✅ 保存成功")


def load_from_database(retriever: Retriever, db_path: str):
    """从数据库加载知识库"""
    print(f"\n从数据库加载知识库: {db_path}")
    retriever.load_knowledge_base(db_path)
    print(f"✅ 已加载 {len(retriever._corpus)} 个知识块")


def list_documents(retriever: Retriever):
    """列出所有文档"""
    print("\n" + "=" * 60)
    print("知识库文档列表")
    print("=" * 60)
    
    if not retriever._corpus:
        print("知识库为空")
        return
    
    # 按文档分组
    docs = {}
    for chunk in retriever._corpus:
        doc_key = f"{chunk['document_name']} {chunk['document_version']}"
        if doc_key not in docs:
            docs[doc_key] = []
        docs[doc_key].append(chunk)
    
    for doc_name, chunks in docs.items():
        print(f"\n📄 {doc_name}")
        print(f"   知识块数量: {len(chunks)}")
        for i, chunk in enumerate(chunks, 1):
            print(f"   {i}. {chunk['section']}")


def test_search(retriever: Retriever, query: str):
    """测试检索"""
    print("\n" + "=" * 60)
    print(f"测试检索: {query}")
    print("=" * 60)
    
    evidences = retriever.retrieve(query, k=3)
    confidence = retriever.calculate_confidence(evidences)
    
    print(f"\n置信度: {confidence:.2f}")
    print(f"找到 {len(evidences)} 条证据:\n")
    
    for i, ev in enumerate(evidences, 1):
        print(f"{i}. 【{ev.document_name} {ev.document_version} - {ev.section}】")
        print(f"   得分: {ev.score:.2f}")
        print(f"   内容: {ev.content[:100]}...")
        print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='知识库管理工具')
    parser.add_argument('--db', default='data/data.db', help='数据库路径')
    parser.add_argument('--action', choices=['add', 'list', 'search', 'rebuild'], 
                       default='add', help='操作类型')
    parser.add_argument('--query', help='搜索查询（用于 search）')
    
    args = parser.parse_args()
    
    # 初始化检索器
    retriever = Retriever()
    
    if args.action == 'add':
        # 添加示例文档
        add_sample_documents(retriever)
        
        # 保存到数据库
        save_to_database(retriever, args.db)
        
        # 验证
        list_documents(retriever)
        
        # 测试检索
        test_search(retriever, "如何安装设备？")
        test_search(retriever, "设备过热怎么办？")
    
    elif args.action == 'list':
        # 加载并列出
        load_from_database(retriever, args.db)
        list_documents(retriever)
    
    elif args.action == 'search':
        if not args.query:
            print("❌ 请提供 --query 参数")
            sys.exit(1)
        
        load_from_database(retriever, args.db)
        test_search(retriever, args.query)
    
    elif args.action == 'rebuild':
        load_from_database(retriever, args.db)
        retriever.rebuild_index()
        print("✅ 索引重建完成")
    
    print("\n" + "=" * 60)
    print("操作完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

