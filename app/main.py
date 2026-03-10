"""
AI 安全警報分類系統
FastAPI 應用程式進入點
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from .models import SecurityAlert, TriageReport
from .database import DatabaseManager
from .logger import AlertLogger
from .ai_classifier import AIClassifier
from .pattern_detector import PatternDetector
from .config import config

# 配置記錄
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化元件
db_manager = DatabaseManager(config.DATABASE_PATH)
alert_logger = AlertLogger(db_manager)
ai_classifier = AIClassifier()
pattern_detector = PatternDetector(alert_logger)

app = FastAPI(
    title="AI 安全警報分類系統",
    description="使用 AI 的自動化安全警報分類",
    version="1.0.0"
)

# 添加 CORS 中介軟體以支援前端
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制為特定來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載靜態檔案目錄（展示頁面）— 使用 CRA 建置輸出
demo_path = Path(__file__).parent.parent / "demo" / "build"
if demo_path.exists():
    app.mount("/demo", StaticFiles(directory=str(demo_path), html=True), name="demo")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """未處理錯誤的全域例外處理器"""
    logger.error(f"未處理的例外：{exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": "發生意外錯誤"
        }
    )

@app.get("/")
async def root():
    return {
        "message": "AI 安全警報分類系統",
        "demo_url": "/demo/index.html",
        "api_docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/triage", response_model=TriageReport)
async def triage_alert(request: Request) -> TriageReport:
    """
    接受安全警報並回傳 AI 驅動的分類分析。
    
    接受：
    - Content-Type: application/json
    - Content-Type: text/plain
    
    回傳：
    - 200：成功分類並附上 TriageReport JSON
    - 400：無效的輸入格式
    - 422：結構驗證失敗
    - 503：OpenAI API 無法使用
    """
    timestamp = datetime.utcnow()
    
    try:
        # 根據 Content-Type 解析請求主體
        content_type = request.headers.get("content-type", "").lower()
        
        if content_type.startswith("application/json"):
            try:
                body = await request.json()
                alert = SecurityAlert(**body)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_json",
                        "detail": "請求主體不是有效的 JSON"
                    }
                )
        elif content_type.startswith("text/plain"):
            body_bytes = await request.body()
            raw_text = body_bytes.decode("utf-8")
            alert = SecurityAlert(raw_data=raw_text)
        else:
            # 預設為 JSON 解析
            try:
                body = await request.json()
                alert = SecurityAlert(**body)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "unsupported_content_type",
                        "detail": "Content-Type 必須是 application/json 或 text/plain"
                    }
                )
        
        # 使用 AI 分類警報
        try:
            report = ai_classifier.classify_alert(alert)
        except RuntimeError as e:
            logger.error(f"AI 分類失敗：{e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "ai_service_unavailable",
                    "detail": "AI 分類服務目前無法使用"
                }
            )
        
        # 偵測模式
        report = pattern_detector.detect_patterns(report, timestamp)
        
        # 記錄分類操作
        request_id = alert_logger.log_triage(alert, report, timestamp)
        logger.info(f"分類完成成功：{request_id}")
        
        return report
        
    except ValidationError as e:
        logger.warning(f"輸入驗證失敗：{e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "validation_error",
                "detail": "輸入驗證失敗",
                "fields": {
                    error["loc"][-1]: [error["msg"]] 
                    for error in e.errors()
                }
            }
        )
    except HTTPException:
        # 重新引發 HTTP 例外
        raise
    except Exception as e:
        logger.error(f"分類端點中的意外錯誤：{e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "detail": "分類過程中發生意外錯誤"
            }
        )