"""
AI 安全警報分類系統的配置管理
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Config:
    """環境變數和設定的配置管理器"""
    
    def __init__(self):
        # 如果存在 .env 檔案，則從中載入環境變數
        self._load_env_file()
        
        self.OPENAI_API_KEY: str = self._get_required_env("OPENAI_API_KEY")
        self.DATABASE_PATH: str = os.getenv("DATABASE_PATH", "triage_logs.db")
        self.PATTERN_DETECTION_WINDOW_HOURS: int = int(
            os.getenv("PATTERN_DETECTION_WINDOW_HOURS", "24")
        )
        self.PATTERN_DETECTION_THRESHOLD: int = int(
            os.getenv("PATTERN_DETECTION_THRESHOLD", "3")
        )
        self.OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        self._validate_config()
    
    def _load_env_file(self):
        """如果存在 .env 檔案，則從中載入環境變數"""
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        except FileNotFoundError:
            pass  # .env 檔案是可選的
    
    def _get_required_env(self, key: str) -> str:
        """取得必要的環境變數或引發錯誤"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"必要的環境變數 {key} 未設定")
        return value
    
    def _validate_config(self) -> None:
        """驗證配置值"""
        if self.PATTERN_DETECTION_WINDOW_HOURS <= 0:
            raise ValueError("PATTERN_DETECTION_WINDOW_HOURS 必須為正數")
        
        if self.PATTERN_DETECTION_THRESHOLD <= 0:
            raise ValueError("PATTERN_DETECTION_THRESHOLD 必須為正數")
        
        if not self.OPENAI_MODEL:
            raise ValueError("OPENAI_MODEL 不能為空")
        
        logger.info("配置驗證成功")
    
    def __repr__(self) -> str:
        return (
            f"Config("
            f"DATABASE_PATH='{self.DATABASE_PATH}', "
            f"PATTERN_DETECTION_WINDOW_HOURS={self.PATTERN_DETECTION_WINDOW_HOURS}, "
            f"PATTERN_DETECTION_THRESHOLD={self.PATTERN_DETECTION_THRESHOLD}, "
            f"OPENAI_MODEL='{self.OPENAI_MODEL}'"
            f")"
        )


# 全域配置實例
config = Config()