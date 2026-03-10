"""
識別重複警報類型的模式偵測功能
"""

import logging
from datetime import datetime
from typing import List

from .models import TriageReport
from .logger import AlertLogger
from .config import config

logger = logging.getLogger(__name__)


class PatternDetector:
    """在時間視窗內識別重複的警報模式"""
    
    def __init__(self, alert_logger: AlertLogger):
        self.alert_logger = alert_logger
        self.window_hours = config.PATTERN_DETECTION_WINDOW_HOURS
        self.threshold = config.PATTERN_DETECTION_THRESHOLD
    
    def detect_patterns(
        self, 
        report: TriageReport, 
        timestamp: datetime
    ) -> TriageReport:
        """
        檢查重複警報並以模式資料豐富化報告。
        
        Args:
            report: 來自 AI_Classifier 的初始分類報告
            timestamp: 當前請求時間戳記
            
        Returns:
            包含 pattern_detected 旗標和元資料的豐富化報告
        """
        try:
            # 查詢資料庫中時間視窗內的匹配警報
            recent_alerts = self.alert_logger.get_recent_alerts(
                threat_classification=report.threat_classification,
                hours_back=self.window_hours,
                from_timestamp=timestamp
            )
            
            # 計算出現次數（包括當前的）
            occurrence_count = len(recent_alerts) + 1
            
            # 檢查是否達到模式閾值
            if occurrence_count >= self.threshold:
                # 從近期警報中提取時間戳記
                pattern_timestamps = [alert.timestamp for alert in recent_alerts]
                
                # 以模式資訊豐富化報告
                report.pattern_detected = True
                report.pattern_count = occurrence_count
                report.pattern_timestamps = pattern_timestamps
                
                logger.info(
                    f"偵測到模式：在 {self.window_hours} 小時內出現 {occurrence_count} 次 "
                    f"'{report.threat_classification}'"
                )
            else:
                # 未偵測到模式
                report.pattern_detected = False
                report.pattern_count = None
                report.pattern_timestamps = None
                
                logger.debug(
                    f"未偵測到模式：'{report.threat_classification}' 出現 {occurrence_count} 次 "
                    f"（閾值：{self.threshold}）"
                )
            
            return report
            
        except Exception as e:
            logger.error(f"模式偵測失敗：{e}")
            # 發生錯誤時，回傳不含模式偵測的報告
            report.pattern_detected = False
            report.pattern_count = None
            report.pattern_timestamps = None
            return report