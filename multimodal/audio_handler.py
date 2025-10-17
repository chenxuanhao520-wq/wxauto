"""
语音处理模块
支持多种ASR方案
"""
import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioHandler:
    """
    语音处理器
    
    支持的ASR方案：
    1. FunASR（本地，推荐，免费）
    2. Whisper（本地，OpenAI开源）
    3. 百度ASR（云端，付费）
    """
    
    def __init__(
        self,
        provider: str = "funasr",
        model_name: str = "paraformer-zh",
        api_key: Optional[str] = None
    ):
        """
        初始化语音处理器
        
        Args:
            provider: ASR提供商（funasr/whisper/baidu）
            model_name: 模型名称
            api_key: API密钥（云端ASR需要）
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self._model = None
        
        logger.info(f"语音处理器初始化: provider={provider}")
    
    def transcribe(self, audio_file: str) -> Optional[str]:
        """
        语音转文字
        
        Args:
            audio_file: 语音文件路径
        
        Returns:
            识别的文本，失败返回None
        """
        if not Path(audio_file).exists():
            logger.error(f"语音文件不存在: {audio_file}")
            return None
        
        try:
            if self.provider == "funasr":
                return self._transcribe_funasr(audio_file)
            elif self.provider == "whisper":
                return self._transcribe_whisper(audio_file)
            elif self.provider == "baidu":
                return self._transcribe_baidu(audio_file)
            else:
                logger.error(f"不支持的ASR提供商: {self.provider}")
                return None
                
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return None
    
    def _transcribe_funasr(self, audio_file: str) -> str:
        """使用FunASR识别（推荐）"""
        try:
            from funasr import AutoModel
        except ImportError:
            raise ImportError(
                "FunASR未安装，请运行: pip install funasr\n"
                "或切换到其他ASR提供商"
            )
        
        # 懒加载模型
        if self._model is None:
            logger.info(f"加载FunASR模型: {self.model_name}（首次会下载）...")
            self._model = AutoModel(model=self.model_name)
            logger.info("FunASR模型加载完成")
        
        # 识别
        result = self._model.generate(input=audio_file)
        
        # 提取文本
        if isinstance(result, list) and len(result) > 0:
            text = result[0].get('text', '')
        elif isinstance(result, dict):
            text = result.get('text', '')
        else:
            text = str(result)
        
        logger.info(f"语音识别成功（FunASR）: {len(text)}字符")
        return text
    
    def _transcribe_whisper(self, audio_file: str) -> str:
        """使用Whisper识别"""
        try:
            import whisper
        except ImportError:
            raise ImportError(
                "Whisper未安装，请运行: pip install openai-whisper\n"
                "或切换到其他ASR提供商"
            )
        
        # 懒加载模型
        if self._model is None:
            logger.info("加载Whisper模型（首次会下载）...")
            self._model = whisper.load_model("base")  # 或 "small"/"medium"
            logger.info("Whisper模型加载完成")
        
        # 识别
        result = self._model.transcribe(audio_file, language="zh")
        text = result['text']
        
        logger.info(f"语音识别成功（Whisper）: {len(text)}字符")
        return text
    
    def _transcribe_baidu(self, audio_file: str) -> str:
        """使用百度ASR识别（需要API Key）"""
        if not self.api_key or ':' not in self.api_key:
            raise ValueError(
                "百度ASR需要API Key，格式：api_key:secret_key\n"
                "或设置环境变量：BAIDU_ASR_KEY"
            )
        
        import requests
        import json
        
        api_key, secret_key = self.api_key.split(':', 1)
        
        # 1. 获取access_token
        token_url = (
            "https://aip.baidubce.com/oauth/2.0/token?"
            f"grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
        )
        
        token_response = requests.get(token_url)
        access_token = token_response.json()['access_token']
        
        # 2. 读取音频
        with open(audio_file, 'rb') as f:
            audio_data = f.read()
        
        # 3. 识别
        url = (
            "https://vop.baidu.com/server_api"
            f"?dev_pid=1537&cuid=python&token={access_token}"
        )
        
        # 需要pcm格式，这里简化处理
        headers = {'Content-Type': 'audio/pcm;rate=16000'}
        
        response = requests.post(url, headers=headers, data=audio_data)
        result = response.json()
        
        if result.get('err_no') == 0:
            text = result['result'][0]
            logger.info(f"语音识别成功（百度）: {len(text)}字符")
            return text
        else:
            logger.error(f"百度ASR识别失败: {result}")
            return ""
    
    def process_wechat_voice(self, voice_file: str) -> Optional[str]:
        """
        处理微信语音文件
        微信语音通常是silk格式，需要先转换
        
        Args:
            voice_file: 微信语音文件（.silk 或 .amr）
        
        Returns:
            识别的文本
        """
        # 检查是否需要格式转换
        file_ext = Path(voice_file).suffix.lower()
        
        if file_ext in ['.silk', '.slk']:
            # silk格式需要转换
            wav_file = self._convert_silk_to_wav(voice_file)
            if not wav_file:
                return None
            
            text = self.transcribe(wav_file)
            
            # 清理临时文件
            Path(wav_file).unlink()
            
            return text
        
        elif file_ext == '.amr':
            # AMR格式（企业微信常用）
            wav_file = self._convert_amr_to_wav(voice_file)
            if not wav_file:
                return None
            
            text = self.transcribe(wav_file)
            
            Path(wav_file).unlink()
            
            return text
        
        else:
            # 其他格式直接识别
            return self.transcribe(voice_file)
    
    def _convert_silk_to_wav(self, silk_file: str) -> Optional[str]:
        """SILK转WAV（需要silk-v3-decoder工具）"""
        import subprocess
        
        wav_file = silk_file.replace('.silk', '.wav').replace('.slk', '.wav')
        
        try:
            # 使用silk-v3-decoder（需要预先安装）
            subprocess.run(
                ['silk-v3-decoder', silk_file, wav_file],
                check=True,
                capture_output=True
            )
            logger.info(f"SILK转换成功: {wav_file}")
            return wav_file
        except Exception as e:
            logger.error(f"SILK转换失败: {e}")
            logger.warning("请安装 silk-v3-decoder 或使用其他语音格式")
            return None
    
    def _convert_amr_to_wav(self, amr_file: str) -> Optional[str]:
        """AMR转WAV（使用ffmpeg）"""
        import subprocess
        
        wav_file = amr_file.replace('.amr', '.wav')
        
        try:
            subprocess.run(
                ['ffmpeg', '-i', amr_file, '-ar', '16000', wav_file, '-y'],
                check=True,
                capture_output=True
            )
            logger.info(f"AMR转换成功: {wav_file}")
            return wav_file
        except Exception as e:
            logger.error(f"AMR转换失败: {e}")
            logger.warning("请安装 ffmpeg")
            return None

