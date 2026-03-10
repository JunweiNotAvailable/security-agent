"""
使用 OpenAI API 的 AI 分類功能
"""

import json
import logging
from typing import Dict, Any
from openai import OpenAI
from openai.types.chat import ChatCompletion

from .models import SecurityAlert, TriageReport, SeverityLevel
from .config import config

logger = logging.getLogger(__name__)


class AIClassifier:
    """處理 OpenAI API 整合以進行安全警報分類"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """建構以安全為重點的 AI 分類系統提示詞"""
        return """您是一位安全分析師助理。請分析以下安全警報並提供結構化評估。

將嚴重程度分類為以下之一：critical、high、medium 或 low
- critical：需要緊急回應的立即威脅（主動入侵、惡意軟體執行）
- high：需要迅速關注的重大威脅（可疑活動、政策違規）
- medium：需要調查的中等威脅（異常、潛在問題）
- low：輕微威脅或資訊性（例行事件、低風險活動）

識別威脅分類（例如：malware、phishing、unauthorized_access、brute_force_attack、data_exfiltration、network_intrusion、policy_violation、suspicious_activity）

根據威脅類型和嚴重程度建議具體的回應行動。

用 1-2 句話提供威脅的簡要摘要。

以 JSON 格式回傳您的分析，包含以下確切欄位：
{
    "severity": "critical|high|medium|low",
    "threat_classification": "specific_threat_type",
    "recommended_action": "specific action to take",
    "summary": "brief description of the threat"
}

確保 JSON 有效且包含所有必填欄位。"""
    
    def classify_alert(self, alert: SecurityAlert) -> TriageReport:
        """
        將警報傳送至 OpenAI API 並解析結構化回應。
        
        Args:
            alert: 已驗證的安全警報資料
            
        Returns:
            包含嚴重程度、分類、行動、摘要的 TriageReport
            
        Raises:
            RuntimeError: 當 API 呼叫失敗或回應無效時
        """
        try:
            # 準備包含警報資料的使用者訊息
            user_message = self._format_alert_for_analysis(alert)
            
            # 呼叫 OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,  # 低溫度以獲得一致的分析
                max_tokens=500,
                timeout=30.0
            )
            
            # 提取並解析回應
            ai_response = response.choices[0].message.content
            if not ai_response:
                raise RuntimeError("OpenAI API 回應為空")
            
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            logger.error(f"OpenAI API 呼叫失敗：{e}")
            raise RuntimeError(f"AI 分類失敗：{str(e)}")
    
    def _format_alert_for_analysis(self, alert: SecurityAlert) -> str:
        """格式化安全警報以供 AI 分析"""
        message_parts = [f"安全警報：{alert.raw_data}"]
        
        if alert.source:
            message_parts.append(f"來源：{alert.source}")
        
        if alert.metadata:
            message_parts.append(f"元資料：{json.dumps(alert.metadata, indent=2)}")
        
        return "\n\n".join(message_parts)
    
    def _parse_ai_response(self, response: str) -> TriageReport:
        """將 AI 回應解析為 TriageReport 結構"""
        try:
            # 嘗試從回應中提取 JSON
            response_data = json.loads(response.strip())
            
            # 驗證必填欄位
            required_fields = ["severity", "threat_classification", "recommended_action", "summary"]
            missing_fields = [field for field in required_fields if field not in response_data]
            
            if missing_fields:
                raise ValueError(f"缺少必填欄位：{missing_fields}")
            
            # 驗證嚴重程度
            severity = response_data["severity"].lower()
            if severity not in [level.value for level in SeverityLevel]:
                logger.warning(f"無效的嚴重程度 '{severity}'，預設為 'medium'")
                severity = "medium"
            
            # 建立並回傳 TriageReport
            return TriageReport(
                severity=SeverityLevel(severity),
                threat_classification=response_data["threat_classification"],
                recommended_action=response_data["recommended_action"],
                summary=response_data["summary"]
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"無法將 AI 回應解析為 JSON：{e}")
            logger.error(f"原始回應：{response}")
            raise RuntimeError("AI 回應不是有效的 JSON")
        
        except ValueError as e:
            logger.error(f"AI 回應驗證失敗：{e}")
            logger.error(f"回應資料：{response_data}")
            raise RuntimeError(f"AI 回應驗證失敗：{str(e)}")
        
        except Exception as e:
            logger.error(f"解析 AI 回應時發生意外錯誤：{e}")
            raise RuntimeError(f"無法解析 AI 回應：{str(e)}")