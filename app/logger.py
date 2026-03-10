"""
AI 安全警報分類系統的警報記錄功能
"""

import sqlite3
import logging
import uuid
from datetime import datetime
from typing import Optional

from .models import SecurityAlert, TriageReport, AlertLogEntry
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class AlertLogger:
    """處理所有分類操作到資料庫的持久化"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def log_triage(
        self, 
        alert: SecurityAlert, 
        report: TriageReport, 
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        將分類操作持久化到資料庫。
        
        Args:
            alert: 原始警報輸入
            report: 生成的分類報告
            timestamp: 請求時間戳記（預設為當前時間）
            
        Returns:
            request_id: 此請求的唯一識別碼
            
        Note: 錯誤會被記錄但不會引發例外
        """
        request_id = str(uuid.uuid4())
        
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO triage_logs (
                        request_id, timestamp, raw_input, severity,
                        threat_classification, recommended_action, summary,
                        pattern_detected, pattern_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    request_id,
                    timestamp.timestamp(),  # 儲存為帶毫秒的 Unix 時間戳記
                    alert.raw_data,
                    report.severity.value,
                    report.threat_classification,
                    report.recommended_action,
                    report.summary,
                    1 if report.pattern_detected else 0,  # SQLite 布林值為整數
                    report.pattern_count
                ))
                
                conn.commit()
                logger.info(f"成功記錄分類操作 {request_id}")
                
        except sqlite3.Error as e:
            logger.error(f"請求 {request_id} 的資料庫寫入失敗：{e}")
            # 不引發例外 - 記錄失敗不應阻止分類完成
        except Exception as e:
            logger.error(f"記錄請求 {request_id} 時發生意外錯誤：{e}")
            # 不引發例外 - 記錄失敗不應阻止分類完成
        
        return request_id
    
    def get_recent_alerts(
        self, 
        threat_classification: str, 
        hours_back: int = 24,
        from_timestamp: Optional[datetime] = None
    ) -> list[AlertLogEntry]:
        """
        檢索具有匹配威脅分類的近期警報。
        
        Args:
            threat_classification: 要匹配的威脅類型
            hours_back: 回溯搜尋的小時數
            from_timestamp: 參考時間戳記（預設為當前時間）
            
        Returns:
            匹配的警報日誌條目列表
        """
        if from_timestamp is None:
            from_timestamp = datetime.utcnow()
        
        cutoff_timestamp = from_timestamp.timestamp() - (hours_back * 3600)
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT request_id, timestamp, raw_input, severity,
                           threat_classification, recommended_action, summary,
                           pattern_detected, pattern_count
                    FROM triage_logs
                    WHERE threat_classification = ? 
                      AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (threat_classification, cutoff_timestamp))
                
                results = []
                for row in cursor.fetchall():
                    try:
                        entry = AlertLogEntry(
                            request_id=row[0],
                            timestamp=datetime.fromtimestamp(row[1]),
                            raw_input=row[2],
                            severity=row[3],
                            threat_classification=row[4],
                            recommended_action=row[5],
                            summary=row[6],
                            pattern_detected=bool(row[7]),
                            pattern_count=row[8]
                        )
                        results.append(entry)
                    except Exception as e:
                        logger.warning(f"跳過無效的日誌條目：{e}")
                        continue
                
                return results
                
        except sqlite3.Error as e:
            logger.error(f"資料庫查詢失敗：{e}")
            return []
        except Exception as e:
            logger.error(f"查詢近期警報時發生意外錯誤：{e}")
            return []