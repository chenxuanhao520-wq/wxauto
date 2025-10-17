"""
图片处理模块
支持OCR和视觉理解
"""
import os
import base64
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ImageHandler:
    """
    图片处理器
    
    支持的处理方式：
    1. OCR提取文字（PaddleOCR，推荐）
    2. 视觉理解（GPT-4V/Claude 3/Gemini）
    """
    
    def __init__(
        self,
        ocr_enabled: bool = True,
        vision_enabled: bool = False,
        vision_provider: str = "gpt4v",
        api_key: Optional[str] = None
    ):
        """
        初始化图片处理器
        
        Args:
            ocr_enabled: 是否启用OCR
            vision_enabled: 是否启用视觉理解
            vision_provider: 视觉模型（gpt4v/claude/gemini）
            api_key: API密钥
        """
        self.ocr_enabled = ocr_enabled
        self.vision_enabled = vision_enabled
        self.vision_provider = vision_provider
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        self._ocr_model = None
        
        logger.info(
            f"图片处理器初始化: ocr={ocr_enabled}, vision={vision_enabled}"
        )
    
    def process_image(
        self,
        image_file: str,
        context_hint: str = ""
    ) -> Dict[str, Any]:
        """
        处理图片（OCR + 可选的视觉理解）
        
        Args:
            image_file: 图片文件路径
            context_hint: 上下文提示（如："这是充电桩故障截图"）
        
        Returns:
            {
                'text': str,           # 提取的文字
                'vision_result': str,  # 视觉理解结果（如果启用）
                'metadata': dict       # 元数据
            }
        """
        if not Path(image_file).exists():
            logger.error(f"图片文件不存在: {image_file}")
            return {'text': '', 'vision_result': '', 'metadata': {}}
        
        result = {
            'text': '',
            'vision_result': '',
            'metadata': {
                'file': image_file,
                'size': os.path.getsize(image_file)
            }
        }
        
        # 1. OCR提取文字
        if self.ocr_enabled:
            try:
                ocr_text = self._ocr_extract(image_file)
                result['text'] = ocr_text
                result['metadata']['ocr_chars'] = len(ocr_text)
                logger.info(f"OCR识别成功: {len(ocr_text)}字符")
            except Exception as e:
                logger.error(f"OCR识别失败: {e}")
        
        # 2. 视觉理解（可选）
        if self.vision_enabled:
            try:
                vision_text = self._vision_understand(image_file, context_hint)
                result['vision_result'] = vision_text
                result['metadata']['vision_provider'] = self.vision_provider
                logger.info(f"视觉理解成功: {len(vision_text)}字符")
            except Exception as e:
                logger.error(f"视觉理解失败: {e}")
        
        return result
    
    def _ocr_extract(self, image_file: str) -> str:
        """
        使用PaddleOCR提取文字
        
        Args:
            image_file: 图片路径
        
        Returns:
            提取的文本
        """
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            raise ImportError(
                "PaddleOCR未安装，请运行: pip install paddleocr\n"
                "这是处理图片的必需依赖"
            )
        
        # 懒加载OCR模型
        if self._ocr_model is None:
            logger.info("加载PaddleOCR模型（首次会下载）...")
            self._ocr_model = PaddleOCR(
                use_angle_cls=True,
                lang='ch',
                show_log=False
            )
            logger.info("PaddleOCR模型加载完成")
        
        # OCR识别
        result = self._ocr_model.ocr(image_file, cls=True)
        
        # 提取文本
        text_lines = []
        if result and result[0]:
            for line in result[0]:
                if len(line) >= 2:
                    text = line[1][0]
                    confidence = line[1][1]
                    
                    # 只保留置信度>0.5的文本
                    if confidence > 0.5:
                        text_lines.append(text)
        
        text = '\n'.join(text_lines)
        return text
    
    def _vision_understand(self, image_file: str, context_hint: str) -> str:
        """
        使用视觉大模型理解图片
        
        Args:
            image_file: 图片路径
            context_hint: 上下文提示
        
        Returns:
            理解结果
        """
        if self.vision_provider == "gpt4v":
            return self._vision_gpt4v(image_file, context_hint)
        elif self.vision_provider == "claude":
            return self._vision_claude(image_file, context_hint)
        elif self.vision_provider == "gemini":
            return self._vision_gemini(image_file, context_hint)
        else:
            logger.error(f"不支持的视觉模型: {self.vision_provider}")
            return ""
    
    def _vision_gpt4v(self, image_file: str, context_hint: str) -> str:
        """GPT-4V视觉理解"""
        try:
            import openai
        except ImportError:
            raise ImportError("openai未安装")
        
        # 读取并编码图片
        with open(image_file, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        client = openai.OpenAI(api_key=self.api_key)
        
        # 构建prompt
        prompt = context_hint or "请详细描述图片内容，特别关注任何错误信息、故障代码、指示灯状态等。"
        
        response = client.chat.completions.create(
            model="gpt-4o",  # 支持视觉
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    def _vision_claude(self, image_file: str, context_hint: str) -> str:
        """Claude 3视觉理解"""
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic未安装，请运行: pip install anthropic")
        
        # 读取并编码图片
        with open(image_file, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')
        
        # 判断图片格式
        ext = Path(image_file).suffix.lower()
        media_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }.get(ext, 'image/jpeg')
        
        client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        
        prompt = context_hint or "请详细描述图片内容，特别关注错误信息和故障代码。"
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        return response.content[0].text
    
    def _vision_gemini(self, image_file: str, context_hint: str) -> str:
        """Gemini Pro Vision理解"""
        # Gemini的Python SDK使用方式
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai未安装")
        
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 读取图片
        import PIL.Image
        img = PIL.Image.open(image_file)
        
        prompt = context_hint or "请描述图片内容，特别关注错误信息。"
        
        response = model.generate_content([prompt, img])
        
        return response.text
    
    def extract_fault_code(self, text: str) -> List[str]:
        """
        从文本中提取故障代码
        
        Args:
            text: OCR提取的文本
        
        Returns:
            故障代码列表
        """
        import re
        
        # 常见故障代码格式
        patterns = [
            r'[EF]\d{2,3}',  # E03, F123
            r'故障代码[：:]\s*([A-Z]\d+)',
            r'错误[：:]\s*([A-Z0-9]+)',
            r'ERROR[：:]\s*([A-Z0-9]+)',
        ]
        
        fault_codes = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            fault_codes.extend(matches)
        
        # 去重
        fault_codes = list(set(fault_codes))
        
        if fault_codes:
            logger.info(f"提取到故障代码: {fault_codes}")
        
        return fault_codes

