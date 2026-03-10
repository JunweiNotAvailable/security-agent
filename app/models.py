"""
AI 安全警報分類系統的資料模型
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    """安全警報嚴重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SecurityAlert(BaseModel):
    """
    安全警報資料的輸入結構。
    支援結構化 JSON 和純文字警報。
    """
    raw_data: str = Field(..., description="原始警報內容", min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="可選的結構化元資料"
    )
    source: Optional[str] = Field(
        default=None,
        description="警報來源系統識別碼"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "raw_data": "來自 IP 192.168.1.100 的登入失敗嘗試",
                "metadata": {"ip": "192.168.1.100", "user": "admin"},
                "source": "auth_system"
            }
        }
    )


class TriageReport(BaseModel):
    """
    AI 生成的分類分析輸出結構。
    """
    severity: SeverityLevel = Field(..., description="警報嚴重程度")
    threat_classification: str = Field(
        ..., 
        description="識別出的安全威脅類型"
    )
    recommended_action: str = Field(
        ..., 
        description="建議的回應行動"
    )
    summary: str = Field(..., description="人類可讀的分析")
    pattern_detected: bool = Field(
        default=False,
        description="指示重複警報模式的旗標"
    )
    pattern_count: Optional[int] = Field(
        default=None,
        description="偵測視窗內相似警報的數量"
    )
    pattern_timestamps: Optional[List[datetime]] = Field(
        default=None,
        description="先前匹配警報的時間戳記"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "severity": "high",
                "threat_classification": "brute_force_attack",
                "recommended_action": "封鎖 IP 位址並重設使用者密碼",
                "summary": "偵測到來自單一 IP 的多次登入失敗嘗試",
                "pattern_detected": True,
                "pattern_count": 5,
                "pattern_timestamps": ["2024-01-15T10:30:00Z", "2024-01-15T11:45:00Z"]
            }
        }
    )


class AlertLogEntry(BaseModel):
    """
    資料庫日誌條目結構。
    """
    request_id: str
    timestamp: datetime
    raw_input: str
    severity: str
    threat_classification: str
    recommended_action: str
    summary: str
    pattern_detected: bool
    pattern_count: Optional[int] = None