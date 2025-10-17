#!/usr/bin/env python3
"""
知识库文档上传工具
支持批量上传 PDF、DOC、DOCX、图片等格式
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from kb_service.document_processor import DocumentProcessor
from kb_service.embeddings import BGEM3Embeddings
from kb_service.vector_store import ChromaStore


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def upload_single_file(
    file_path: str,
    document_name: str = None,
    version: str = "v1.0",
    use_vector: bool = True
):
    """
    上传单个文件
    
    Args:
        file_path: 文件路径
        document_name: 文档名称
        version: 版本
        use_vector: 是否使用向量检索
    """
    print_header(f"上传文档: {file_path}")
    
    try:
        # 1. 处理文档
        print("步骤1：解析文档...")
        processor = DocumentProcessor(use_ocr=True)
        result = processor.process_file(
            file_path=file_path,
            document_name=document_name,
            document_version=version,
            chunk_size=500,
            chunk_overlap=50
        )
        
        print(f"  ✅ 文档名称: {result['document_name']}")
        print(f"  ✅ 版本: {result['document_version']}")
        print(f"  ✅ 总字符: {result['total_chars']}")
        print(f"  ✅ 分段数: {len(result['chunks'])}")
        
        # 2. 保存到SQLite（简单模式）
        if not use_vector:
            print("\n步骤2：保存到SQLite...")
            from storage.db import Database
            import sqlite3
            
            db = Database("data/data.db")
            conn = db.connect()
            cursor = conn.cursor()
            
            for chunk in result['chunks']:
                keywords_str = ','.join(chunk.get('keywords', []))
                
                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge_chunks
                    (chunk_id, document_name, document_version, section, content, keywords)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    chunk['chunk_id'],
                    chunk['document_name'],
                    chunk['document_version'],
                    chunk['section'],
                    chunk['content'],
                    keywords_str
                ))
            
            conn.commit()
            db.close()
            
            print(f"  ✅ 已保存到 SQLite: {len(result['chunks'])} 个分段")
        
        # 3. 生成向量并保存（向量模式）
        else:
            print("\n步骤2：生成向量嵌入...")
            
            try:
                embeddings_model = BGEM3Embeddings()
                
                # 提取文本
                texts = [chunk['content'] for chunk in result['chunks']]
                metadatas = [
                    {
                        'document_name': chunk['document_name'],
                        'document_version': chunk['document_version'],
                        'section': chunk['section'],
                        'keywords': ','.join(chunk.get('keywords', []))
                    }
                    for chunk in result['chunks']
                ]
                ids = [chunk['chunk_id'] for chunk in result['chunks']]
                
                # 生成嵌入
                print(f"  生成嵌入向量（使用BGE-M3）...")
                embeddings = embeddings_model.embed_documents(texts)
                
                print(f"  ✅ 嵌入生成完成: {len(embeddings)} 个向量")
                
                # 保存到向量数据库
                print("\n步骤3：保存到向量数据库...")
                vector_store = ChromaStore(persist_directory="data/chroma_db")
                
                vector_store.add_documents(
                    collection_name="knowledge_base",
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
                
                count = vector_store.get_count("knowledge_base")
                print(f"  ✅ 已保存到 Chroma: 当前总计 {count} 个分段")
                
            except ImportError as e:
                print(f"  ⚠️  向量库未安装: {e}")
                print("  回退到简单模式（仅保存到SQLite）...")
                upload_single_file(file_path, document_name, version, use_vector=False)
                return
        
        print("\n" + "=" * 60)
        print("✅ 文档上传完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()


def upload_directory(
    directory: str,
    version: str = "v1.0",
    pattern: str = "*",
    use_vector: bool = True
):
    """
    批量上传目录中的文件
    
    Args:
        directory: 目录路径
        version: 统一版本号
        pattern: 文件匹配模式
        use_vector: 是否使用向量检索
    """
    print_header(f"批量上传目录: {directory}")
    
    path = Path(directory)
    if not path.is_dir():
        print(f"❌ 目录不存在: {directory}")
        return
    
    # 支持的格式
    supported_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
    
    # 查找文件
    files = []
    for ext in supported_extensions:
        files.extend(path.glob(f"**/*{ext}"))
    
    if not files:
        print(f"❌ 未找到支持的文件")
        print(f"   支持格式: {', '.join(supported_extensions)}")
        return
    
    print(f"找到 {len(files)} 个文件:\n")
    for f in files:
        print(f"  - {f.name}")
    
    print("\n开始上传...\n")
    
    # 逐个上传
    success_count = 0
    for file in files:
        try:
            upload_single_file(
                file_path=str(file),
                document_name=file.stem,
                version=version,
                use_vector=use_vector
            )
            success_count += 1
        except Exception as e:
            print(f"❌ {file.name} 上传失败: {e}")
            continue
    
    print("\n" + "=" * 60)
    print(f"批量上传完成: {success_count}/{len(files)} 个文件成功")
    print("=" * 60)


def list_documents(use_vector: bool = True):
    """列出已上传的文档"""
    print_header("知识库文档列表")
    
    if use_vector:
        try:
            vector_store = ChromaStore(persist_directory="data/chroma_db")
            count = vector_store.get_count("knowledge_base")
            
            print(f"向量数据库中共有 {count} 个知识分段")
            print("（Chroma不支持直接列出文档，请使用SQLite模式查看详情）")
            
        except Exception as e:
            print(f"❌ 查询向量数据库失败: {e}")
    
    # 从SQLite查询
    try:
        import sqlite3
        
        conn = sqlite3.connect("data/data.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT document_name, document_version, COUNT(*) as chunk_count
            FROM knowledge_chunks
            GROUP BY document_name, document_version
            ORDER BY document_name
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            print(f"\nSQLite数据库中的文档:\n")
            for name, version, count in rows:
                print(f"  📄 {name} {version} ({count} 个分段)")
        else:
            print("\nSQLite数据库中暂无文档")
            
    except Exception as e:
        print(f"❌ 查询SQLite失败: {e}")


def search_test(query: str, use_vector: bool = True):
    """测试检索"""
    print_header(f"测试检索: {query}")
    
    if use_vector:
        try:
            # 使用向量检索
            from kb_service.embeddings import BGEM3Embeddings
            from kb_service.vector_store import ChromaStore
            
            print("使用向量检索（BGE-M3）...\n")
            
            embeddings_model = BGEM3Embeddings()
            query_embedding = embeddings_model.embed_query(query)
            
            vector_store = ChromaStore(persist_directory="data/chroma_db")
            results = vector_store.search(
                collection_name="knowledge_base",
                query_embedding=query_embedding,
                n_results=5
            )
            
            if results and results['documents']:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                
                print(f"找到 {len(documents)} 条相关结果:\n")
                
                for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), 1):
                    score = 1 - dist  # 转换为相似度
                    print(f"{i}. 【{meta['document_name']} {meta.get('document_version', '')} - {meta.get('section', '')}】")
                    print(f"   相似度: {score:.3f}")
                    print(f"   内容: {doc[:100]}...")
                    print()
            else:
                print("未找到相关结果")
                
        except ImportError as e:
            print(f"⚠️  向量检索不可用: {e}")
            print("回退到BM25检索...\n")
            use_vector = False
    
    if not use_vector:
        # 使用BM25检索
        from rag.retriever import Retriever
        
        print("使用BM25检索...\n")
        
        retriever = Retriever()
        retriever.load_knowledge_base("data/data.db")
        
        evidences = retriever.retrieve(query, k=5)
        confidence = retriever.calculate_confidence(evidences)
        
        print(f"置信度: {confidence:.2f}\n")
        print(f"找到 {len(evidences)} 条相关结果:\n")
        
        for i, ev in enumerate(evidences, 1):
            print(f"{i}. 【{ev.document_name} {ev.document_version} - {ev.section}】")
            print(f"   得分: {ev.score:.2f}")
            print(f"   内容: {ev.content[:100]}...")
            print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='知识库文档上传工具')
    parser.add_argument('action', choices=['upload', 'upload-dir', 'list', 'search'],
                       help='操作类型')
    parser.add_argument('--file', help='文件路径（upload）')
    parser.add_argument('--dir', help='目录路径（upload-dir）')
    parser.add_argument('--name', help='文档名称（可选）')
    parser.add_argument('--version', default='v1.0', help='版本号')
    parser.add_argument('--query', help='搜索查询（search）')
    parser.add_argument('--mode', choices=['vector', 'simple'], default='vector',
                       help='模式：vector=向量检索, simple=BM25检索')
    
    args = parser.parse_args()
    
    use_vector = (args.mode == 'vector')
    
    print("\n" + "📚 " * 20)
    print("  知识库文档上传工具")
    print("📚 " * 20)
    
    if args.action == 'upload':
        if not args.file:
            print("❌ 请指定 --file 参数")
            sys.exit(1)
        
        upload_single_file(
            file_path=args.file,
            document_name=args.name,
            version=args.version,
            use_vector=use_vector
        )
    
    elif args.action == 'upload-dir':
        if not args.dir:
            print("❌ 请指定 --dir 参数")
            sys.exit(1)
        
        upload_directory(
            directory=args.dir,
            version=args.version,
            use_vector=use_vector
        )
    
    elif args.action == 'list':
        list_documents(use_vector=use_vector)
    
    elif args.action == 'search':
        if not args.query:
            print("❌ 请指定 --query 参数")
            sys.exit(1)
        
        search_test(query=args.query, use_vector=use_vector)


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

