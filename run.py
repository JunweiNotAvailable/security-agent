#!/usr/bin/env python3
"""
AI 安全警報分類系統的主要進入點
"""

import os
import sys
import logging
from pathlib import Path

# 將 app 目錄新增到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """主應用程式進入點"""
    # 設定記錄
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # 匯入並初始化應用程式
        from app.main import app
        from app.config import config
        from app.database import DatabaseManager
        
        # 驗證配置
        logger.info("啟動 AI 安全警報分類系統")
        logger.info(f"配置：{config}")
        
        # 驗證資料庫初始化
        db_manager = DatabaseManager(config.DATABASE_PATH)
        if db_manager.verify_schema():
            logger.info("資料庫結構驗證成功")
        else:
            logger.error("資料庫結構驗證失敗")
            sys.exit(1)
        
        # 啟動伺服器
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
        
    except ValueError as e:
        logger.error(f"配置錯誤：{e}")
        logger.error("請檢查您的環境變數")
        sys.exit(1)
    except Exception as e:
        logger.error(f"應用程式啟動失敗：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()