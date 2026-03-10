"""
AI 安全警報分類系統的資料庫初始化和管理
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """管理警報記錄的 SQLite 資料庫操作"""
    
    def __init__(self, db_path: str = "triage_logs.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self) -> None:
        """
        使用所需結構初始化 SQLite 資料庫。
        如果資料庫檔案不存在則建立。
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 建立主要資料表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS triage_logs (
                        request_id TEXT PRIMARY KEY,
                        timestamp REAL NOT NULL,
                        raw_input TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        threat_classification TEXT NOT NULL,
                        recommended_action TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        pattern_detected INTEGER NOT NULL,
                        pattern_count INTEGER
                    )
                """)
                
                # 建立索引以進行高效查詢
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON triage_logs(timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_threat_classification 
                    ON triage_logs(threat_classification)
                """)
                
                conn.commit()
                logger.info(f"資料庫在 {self.db_path} 初始化成功")
                
        except sqlite3.Error as e:
            logger.error(f"資料庫初始化失敗：{e}")
            raise RuntimeError(f"無法初始化資料庫：{e}")
        except Exception as e:
            logger.error(f"資料庫初始化過程中發生意外錯誤：{e}")
            raise RuntimeError(f"資料庫初始化意外錯誤：{e}")
    
    def get_connection(self) -> sqlite3.Connection:
        """取得資料庫連線"""
        try:
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            logger.error(f"無法連線到資料庫：{e}")
            raise RuntimeError(f"資料庫連線失敗：{e}")
    
    def verify_schema(self) -> bool:
        """驗證資料庫結構是否正確"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 檢查資料表是否存在
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='triage_logs'
                """)
                if not cursor.fetchone():
                    return False
                
                # 檢查資料表結構
                cursor.execute("PRAGMA table_info(triage_logs)")
                columns = {row[1] for row in cursor.fetchall()}
                
                required_columns = {
                    "request_id", "timestamp", "raw_input", "severity",
                    "threat_classification", "recommended_action", 
                    "summary", "pattern_detected", "pattern_count"
                }
                
                if not required_columns.issubset(columns):
                    return False
                
                # 檢查索引
                cursor.execute("PRAGMA index_list(triage_logs)")
                indexes = {row[1] for row in cursor.fetchall()}
                
                required_indexes = {"idx_timestamp", "idx_threat_classification"}
                if not required_indexes.issubset(indexes):
                    return False
                
                return True
                
        except sqlite3.Error as e:
            logger.error(f"結構驗證失敗：{e}")
            return False