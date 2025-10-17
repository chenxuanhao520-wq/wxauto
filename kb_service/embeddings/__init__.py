"""
嵌入模型模块
"""
from .bge_m3 import BGEM3Embeddings
from .openai_embed import OpenAIEmbeddings

__all__ = ['BGEM3Embeddings', 'OpenAIEmbeddings']

