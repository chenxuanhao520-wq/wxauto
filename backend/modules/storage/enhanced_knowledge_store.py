"""
知识库存储优化 - 支持PaddleOCR-VL多模态数据
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedKnowledgeStore:
    """
    增强版知识库存储 - 支持PaddleOCR-VL多模态数据
    
    特性：
    1. 多模态数据存储（文本、表格、公式、图表）
    2. 充电桩行业分类
    3. 智能索引和检索
    4. 版本管理
    """
    
    def __init__(self, db_path: str = "data/enhanced_knowledge.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 文档表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                processing_mode TEXT,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version TEXT DEFAULT 'v1.0',
                industry_category TEXT,
                document_category TEXT,
                confidence_score REAL,
                metadata TEXT,
                status TEXT DEFAULT 'active'
            )
        """)
        
        # 知识块表（支持多模态）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                chunk_id TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                chunk_type TEXT DEFAULT 'text',
                element_type TEXT,
                bbox TEXT,
                confidence REAL,
                keywords TEXT,
                section TEXT,
                char_count INTEGER,
                metadata TEXT,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        """)
        
        # 多模态元素表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS multimodal_elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                element_type TEXT NOT NULL,
                element_content TEXT NOT NULL,
                element_data TEXT,
                bbox TEXT,
                confidence REAL,
                metadata TEXT,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        """)
        
        # 表格数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS table_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                table_id TEXT NOT NULL,
                table_html TEXT,
                table_data TEXT,
                rows_count INTEGER,
                cols_count INTEGER,
                confidence REAL,
                metadata TEXT,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        """)
        
        # 行业分析表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS industry_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                industry_type TEXT,
                document_category TEXT,
                technical_keywords TEXT,
                safety_keywords TEXT,
                compliance_keywords TEXT,
                confidence REAL,
                analysis_data TEXT,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON knowledge_chunks(document_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_type ON knowledge_chunks(chunk_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_elements_type ON multimodal_elements(element_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_industry_category ON industry_analysis(document_category)")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ 增强版知识库数据库初始化完成")
    
    def save_document(self, ocr_result: Dict[str, Any]) -> int:
        """保存OCR处理结果到知识库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 保存文档信息
            cursor.execute("""
                INSERT OR REPLACE INTO documents 
                (file_path, file_name, file_size, file_type, processing_mode, 
                 industry_category, document_category, confidence_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ocr_result["file_path"],
                ocr_result["file_name"],
                ocr_result["file_size"],
                Path(ocr_result["file_path"]).suffix.lower(),
                ocr_result["processing_mode"],
                ocr_result["industry_analysis"].get("industry_type", "unknown"),
                ocr_result["industry_analysis"].get("document_category", "unknown"),
                ocr_result["industry_analysis"].get("confidence", 0.0),
                json.dumps(ocr_result["metadata"], ensure_ascii=False)
            ))
            
            document_id = cursor.lastrowid
            
            # 保存知识块
            if "content" in ocr_result and ocr_result["content"]:
                self._save_text_chunks(cursor, document_id, ocr_result)
            
            # 保存多模态元素
            if "multimodal_data" in ocr_result:
                self._save_multimodal_elements(cursor, document_id, ocr_result["multimodal_data"])
            
            # 保存表格数据
            if "multimodal_data" in ocr_result and "table_elements" in ocr_result["multimodal_data"]:
                self._save_table_data(cursor, document_id, ocr_result["multimodal_data"]["table_elements"])
            
            # 保存行业分析
            self._save_industry_analysis(cursor, document_id, ocr_result["industry_analysis"])
            
            conn.commit()
            logger.info(f"✅ 文档保存成功: {ocr_result['file_name']} (ID: {document_id})")
            
            return document_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ 文档保存失败: {e}")
            raise
        finally:
            conn.close()
    
    def _save_text_chunks(self, cursor, document_id: int, ocr_result: Dict[str, Any]):
        """保存文本知识块"""
        content = ocr_result["content"]
        
        # 简单分段（实际应用中可以使用更智能的分段）
        chunks = self._split_content(content)
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{ocr_result['file_name']}_chunk_{i}"
            
            cursor.execute("""
                INSERT OR REPLACE INTO knowledge_chunks
                (document_id, chunk_id, content, chunk_type, char_count, keywords, section)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id,
                chunk_id,
                chunk,
                "text",
                len(chunk),
                self._extract_keywords(chunk),
                "正文"
            ))
    
    def _save_multimodal_elements(self, cursor, document_id: int, multimodal_data: Dict[str, Any]):
        """保存多模态元素"""
        for element_type in ["text_elements", "table_elements", "formula_elements", "chart_elements"]:
            if element_type in multimodal_data:
                for element in multimodal_data[element_type]:
                    cursor.execute("""
                        INSERT INTO multimodal_elements
                        (document_id, element_type, element_content, element_data, 
                         bbox, confidence, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        document_id,
                        element["type"],
                        element["content"],
                        json.dumps(element, ensure_ascii=False),
                        json.dumps(element.get("bbox", []), ensure_ascii=False),
                        element.get("confidence", 0.0),
                        json.dumps(element.get("metadata", {}), ensure_ascii=False)
                    ))
    
    def _save_table_data(self, cursor, document_id: int, table_elements: List[Dict[str, Any]]):
        """保存表格数据"""
        for i, table in enumerate(table_elements):
            table_id = f"table_{document_id}_{i}"
            
            cursor.execute("""
                INSERT INTO table_data
                (document_id, table_id, table_html, table_data, 
                 rows_count, cols_count, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id,
                table_id,
                table.get("html", ""),
                json.dumps(table, ensure_ascii=False),
                0, 0,  # 实际应用中需要解析表格结构
                table.get("confidence", 0.0),
                json.dumps(table.get("metadata", {}), ensure_ascii=False)
            ))
    
    def _save_industry_analysis(self, cursor, document_id: int, industry_analysis: Dict[str, Any]):
        """保存行业分析结果"""
        cursor.execute("""
            INSERT INTO industry_analysis
            (document_id, industry_type, document_category, technical_keywords,
             safety_keywords, compliance_keywords, confidence, analysis_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document_id,
            industry_analysis.get("industry_type", "unknown"),
            industry_analysis.get("document_category", "unknown"),
            json.dumps(industry_analysis.get("technical_keywords", []), ensure_ascii=False),
            json.dumps(industry_analysis.get("safety_keywords", []), ensure_ascii=False),
            json.dumps(industry_analysis.get("compliance_keywords", []), ensure_ascii=False),
            industry_analysis.get("confidence", 0.0),
            json.dumps(industry_analysis, ensure_ascii=False)
        ))
    
    def _split_content(self, content: str, chunk_size: int = 500) -> List[str]:
        """内容分段"""
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            chunks.append(chunk)
        
        return chunks
    
    def _extract_keywords(self, text: str) -> str:
        """提取关键词（简化版）"""
        # 实际应用中可以使用更复杂的关键词提取算法
        keywords = []
        for category, words in {
            'technical': ['充电桩', '充电站', '功率', '电压', '电流'],
            'safety': ['安全', '防护', '绝缘', '漏电'],
            'maintenance': ['维护', '保养', '检修', '故障']
        }.items():
            for word in words:
                if word in text:
                    keywords.append(word)
        
        return ','.join(keywords)
    
    def search_documents(self, 
                        query: str,
                        document_category: Optional[str] = None,
                        industry_type: Optional[str] = None,
                        limit: int = 10) -> List[Dict[str, Any]]:
        """搜索文档"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = ["d.status = 'active'"]
        params = []
        
        if document_category:
            conditions.append("d.document_category = ?")
            params.append(document_category)
        
        if industry_type:
            conditions.append("d.industry_type = ?")
            params.append(industry_type)
        
        # 文本搜索
        if query:
            conditions.append("(kc.content LIKE ? OR d.file_name LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT DISTINCT d.*, ia.document_category, ia.industry_type
            FROM documents d
            LEFT JOIN knowledge_chunks kc ON d.id = kc.document_id
            LEFT JOIN industry_analysis ia ON d.id = ia.document_id
            WHERE {where_clause}
            ORDER BY d.upload_time DESC
            LIMIT ?
        """, params + [limit])
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "file_path": row[1],
                "file_name": row[2],
                "file_size": row[3],
                "file_type": row[4],
                "processing_mode": row[5],
                "upload_time": row[6],
                "version": row[7],
                "industry_category": row[8],
                "document_category": row[9],
                "confidence_score": row[10],
                "metadata": json.loads(row[11]) if row[11] else {}
            })
        
        conn.close()
        return results
    
    def get_document_stats(self) -> Dict[str, Any]:
        """获取文档统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总文档数
        cursor.execute("SELECT COUNT(*) FROM documents WHERE status = 'active'")
        total_docs = cursor.fetchone()[0]
        
        # 按类型统计
        cursor.execute("""
            SELECT file_type, COUNT(*) 
            FROM documents 
            WHERE status = 'active' 
            GROUP BY file_type
        """)
        type_stats = dict(cursor.fetchall())
        
        # 按行业分类统计
        cursor.execute("""
            SELECT ia.document_category, COUNT(*) 
            FROM documents d
            LEFT JOIN industry_analysis ia ON d.id = ia.document_id
            WHERE d.status = 'active' AND ia.document_category IS NOT NULL
            GROUP BY ia.document_category
        """)
        category_stats = dict(cursor.fetchall())
        
        # 多模态元素统计
        cursor.execute("""
            SELECT element_type, COUNT(*) 
            FROM multimodal_elements 
            GROUP BY element_type
        """)
        element_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total_documents": total_docs,
            "type_distribution": type_stats,
            "category_distribution": category_stats,
            "element_distribution": element_stats
        }
    
    def get_document_details(self, document_id: int) -> Optional[Dict[str, Any]]:
        """获取文档详细信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取文档基本信息
        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        doc_row = cursor.fetchone()
        
        if not doc_row:
            conn.close()
            return None
        
        # 获取知识块
        cursor.execute("SELECT * FROM knowledge_chunks WHERE document_id = ?", (document_id,))
        chunks = cursor.fetchall()
        
        # 获取多模态元素
        cursor.execute("SELECT * FROM multimodal_elements WHERE document_id = ?", (document_id,))
        elements = cursor.fetchall()
        
        # 获取表格数据
        cursor.execute("SELECT * FROM table_data WHERE document_id = ?", (document_id,))
        tables = cursor.fetchall()
        
        # 获取行业分析
        cursor.execute("SELECT * FROM industry_analysis WHERE document_id = ?", (document_id,))
        analysis_row = cursor.fetchone()
        
        conn.close()
        
        return {
            "document": {
                "id": doc_row[0],
                "file_path": doc_row[1],
                "file_name": doc_row[2],
                "file_size": doc_row[3],
                "file_type": doc_row[4],
                "processing_mode": doc_row[5],
                "upload_time": doc_row[6],
                "version": doc_row[7],
                "industry_category": doc_row[8],
                "document_category": doc_row[9],
                "confidence_score": doc_row[10],
                "metadata": json.loads(doc_row[11]) if doc_row[11] else {}
            },
            "chunks": [{"id": c[0], "chunk_id": c[2], "content": c[3], "chunk_type": c[4]} for c in chunks],
            "elements": [{"type": e[2], "content": e[3], "confidence": e[6]} for e in elements],
            "tables": [{"table_id": t[2], "html": t[3], "confidence": t[7]} for t in tables],
            "industry_analysis": {
                "industry_type": analysis_row[2] if analysis_row else None,
                "document_category": analysis_row[3] if analysis_row else None,
                "confidence": analysis_row[8] if analysis_row else 0.0
            } if analysis_row else {}
        }

