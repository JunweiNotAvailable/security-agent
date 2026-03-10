# 設計文件：AI 安全警報分類系統

## 概述

AI 安全警報分類系統是一個基於 Python 的 REST API 服務，使用 OpenAI 的 GPT-4o-mini 模型自動化安全警報分類。系統提供單一端點，接受 JSON 或純文字格式的安全警報，透過 AI 分析處理，並回傳包含嚴重程度、威脅分類和建議行動的結構化分類報告。

架構採用分層方法，在 API 處理、AI 處理、資料持久化和模式偵測之間有清楚的分離。所有元件都使用現代 Python 框架（FastAPI、Pydantic、SQLite）建構，以確保類型安全、效能和可維護性。

主要設計目標：
- 透過 REST API 簡單整合
- 可靠的 AI 驅動分類
- 全面的稽核記錄
- 重複威脅的模式偵測
- 全程類型安全的資料驗證

## 架構

系統由五個主要元件組成，以請求-回應流程組織：

```
┌─────────────────────────────────────────────────────────────────┐
│                        外部客戶端                                │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Alert_Ingestion_API                           │
│                      (FastAPI)                                  │
│  - 輸入驗證 (Pydantic)                                           │
│  - Content-Type 處理 (JSON/text)                                │
│  - HTTP 回應格式化                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │ Security_Alert
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI_Classifier                              │
│  - OpenAI API 整合                                              │
│  - 提示詞工程                                                    │
│  - 回應解析                                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ Triage_Report
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pattern_Detector                             │
│  - 資料庫查詢匹配警報                                             │
│  - 時間視窗計算                                                   │
│  - 模式旗標豐富化                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ 豐富化的 Triage_Report
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Alert_Logger                               │
│  - SQLite 持久化                                                │
│  - 請求/回應關聯                                                 │
│  - 錯誤處理                                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 元件互動流程

1. 客戶端向 `/api/v1/triage` 發送包含警報資料的 HTTP POST
2. Alert_Ingestion_API 根據 Pydantic schema 驗證輸入
3. AI_Classifier 將警報以安全提示詞傳送至 OpenAI API
4. AI_Classifier 將回應解析為結構化的 Triage_Report
5. Pattern_Detector 查詢資料庫中相似的近期警報
6. Pattern_Detector 以模式資訊豐富化報告
7. Alert_Logger 將請求和回應持久化到 SQLite
8. Alert_Ingestion_API 將 JSON 回應回傳給客戶端

## 元件與介面

### Alert_Ingestion_API

**職責：** HTTP 請求處理、輸入驗證、回應格式化

**技術：** FastAPI 框架

**介面：**
```python
@app.post("/api/v1/triage")
async def triage_alert(request: Request) -> TriageReport:
    """
    接受安全警報並回傳 AI 驅動的分類分析。
    
    接受：
    - Content-Type: application/json
    - Content-Type: text/plain
    
    回傳：
    - 200: 成功分類並附上 TriageReport JSON
    - 400: 無效的輸入格式
    - 422: Schema 驗證失敗
    - 503: OpenAI API 無法使用
    """
```

**主要操作：**
- 根據 Content-Type 標頭解析請求主體
- 根據 SecurityAlert Pydantic 模型驗證輸入
- 協調對 AI_Classifier、Pattern_Detector、Alert_Logger 的呼叫
- 以適當的狀態碼格式化 HTTP 回應
- 處理例外並轉換為 HTTP 錯誤回應

### AI_Classifier

**職責：** OpenAI API 整合與回應解析

**技術：** OpenAI Python SDK

**介面：**
```python
class AIClassifier:
    def classify_alert(self, alert: SecurityAlert) -> TriageReport:
        """
        將警報傳送至 OpenAI API 並解析結構化回應。
        
        Args:
            alert: 已驗證的安全警報資料
            
        Returns:
            包含 severity、classification、action、summary 的 TriageReport
            
        Raises:
            OpenAIAPIError: 當 API 呼叫失敗時
        """
```

**系統提示詞設計：**
```
You are a security analyst assistant. Analyze the following security alert 
and provide a structured assessment.

Classify the severity as: critical, high, medium, or low
Identify the threat classification (e.g., malware, phishing, unauthorized access)
Recommend a specific response action
Provide a brief summary of the threat

Return your analysis in JSON format with these exact fields:
- severity
- threat_classification
- recommended_action
- summary
```

**主要操作：**
- 使用警報資料和系統指令建構提示詞
- 使用 gpt-4o-mini 模型呼叫 OpenAI API
- 從 AI 模型解析 JSON 回應
- 驗證回應結構
- 處理 API 錯誤和逾時

### Pattern_Detector

**職責：** 識別重複出現的警報模式

**介面：**
```python
class PatternDetector:
    def detect_patterns(self, report: TriageReport, 
                       timestamp: datetime) -> TriageReport:
        """
        檢查重複出現的警報並以模式資料豐富化報告。
        
        Args:
            report: 來自 AI_Classifier 的初始分類報告
            timestamp: 當前請求時間戳記
            
        Returns:
            包含 pattern_detected 旗標和元資料的豐富化報告
        """
```

**主要操作：**
- 查詢資料庫中具有匹配 threat_classification 的警報
- 將結果篩選至從當前時間戳記起的 24 小時視窗
- 計算匹配的出現次數
- 如果計數 >= 3，則新增 pattern_detected 旗標
- 在報告中包含出現次數和時間戳記

### Alert_Logger

**職責：** 將所有分類操作持久化到資料庫

**技術：** SQLite 搭配 Python sqlite3 模組

**介面：**
```python
class AlertLogger:
    def log_triage(self, request_id: str, alert: SecurityAlert, 
                   report: TriageReport, timestamp: datetime) -> None:
        """
        將分類操作持久化到資料庫。
        
        Args:
            request_id: 此請求的唯一識別碼
            alert: 原始警報輸入
            report: 生成的分類報告
            timestamp: 請求時間戳記
            
        Note: 錯誤會被記錄但不會引發例外
        """
```

**主要操作：**
- 生成唯一的 request_id (UUID)
- 插入包含所有請求/回應資料的日誌條目
- 優雅地處理資料庫連線錯誤
- 確保啟動時資料庫結構存在
- 建立索引以進行高效查詢

### Configuration Manager

**職責：** 管理環境配置和機密資訊

**介面：**
```python
class Config:
    OPENAI_API_KEY: str
    DATABASE_PATH: str = "triage_logs.db"
    PATTERN_DETECTION_WINDOW_HOURS: int = 24
    PATTERN_DETECTION_THRESHOLD: int = 3
    OPENAI_MODEL: str = "gpt-4o-mini"
```

**主要操作：**
- 從環境變數載入 OpenAI API 金鑰
- 為可配置參數提供預設值
- 在啟動時驗證必要的配置

## 資料模型

### SecurityAlert (輸入結構)

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class SecurityAlert(BaseModel):
    """
    安全警報資料的輸入結構。
    支援結構化 JSON 和純文字警報。
    """
    raw_data: str = Field(..., description="原始警報內容")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="可選的結構化元資料"
    )
    source: Optional[str] = Field(
        default=None,
        description="警報來源系統識別碼"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "raw_data": "Failed login attempt from IP 192.168.1.100",
                "metadata": {"ip": "192.168.1.100", "user": "admin"},
                "source": "auth_system"
            }
        }
```

### TriageReport (輸出結構)

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

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
    
    class Config:
        json_schema_extra = {
            "example": {
                "severity": "high",
                "threat_classification": "brute_force_attack",
                "recommended_action": "Block IP address and reset user password",
                "summary": "Multiple failed login attempts detected from single IP",
                "pattern_detected": True,
                "pattern_count": 5,
                "pattern_timestamps": ["2024-01-15T10:30:00Z", "2024-01-15T11:45:00Z"]
            }
        }
```

### AlertLogEntry (資料庫結構)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AlertLogEntry(BaseModel):
    """
    資料庫日誌條目的結構。
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
```

### Database Schema (SQLite)

```sql
CREATE TABLE IF NOT EXISTS triage_logs (
    request_id TEXT PRIMARY KEY,
    timestamp REAL NOT NULL,  -- Unix 時間戳記（含毫秒）
    raw_input TEXT NOT NULL,
    severity TEXT NOT NULL,
    threat_classification TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    summary TEXT NOT NULL,
    pattern_detected INTEGER NOT NULL,  -- 布林值以 0/1 表示
    pattern_count INTEGER
);

CREATE INDEX IF NOT EXISTS idx_timestamp 
ON triage_logs(timestamp);

CREATE INDEX IF NOT EXISTS idx_threat_classification 
ON triage_logs(threat_classification);
```


## 錯誤處理

系統在多個層級實作深度防禦錯誤處理：

### API 層（Alert_Ingestion_API）

**輸入驗證錯誤：**
- HTTP 400：格式錯誤的請求主體（無效的 JSON、無法解析的內容）
- HTTP 422：結構驗證失敗（缺少必填欄位、錯誤的類型）
- 回應包含來自 Pydantic 的欄位層級錯誤詳情

**處理錯誤：**
- HTTP 503：OpenAI API 無法使用或逾時
- HTTP 500：意外的內部錯誤
- 所有例外都會被捕獲並轉換為適當的 HTTP 回應

**錯誤回應格式：**
```json
{
    "error": "錯誤類型",
    "detail": "人類可讀的錯誤訊息",
    "fields": {  // 僅用於驗證錯誤
        "field_name": ["錯誤訊息"]
    }
}
```

### AI Classifier 層

**OpenAI API 錯誤：**
- 網路逾時：重試一次，然後以 503 失敗
- 速率限制：回傳 503 並附上重試建議
- 無效的 API 金鑰：記錄錯誤並回傳 503
- 格式錯誤的回應：記錄警告並回傳 503

**回應解析錯誤：**
- 缺少必填欄位：記錄警告並回傳 503
- 無效的 severity 值：預設為 "medium" 並記錄警告
- 非 JSON 回應：記錄錯誤並回傳 503

### Pattern Detector 層

**資料庫查詢錯誤：**
- 連線失敗：記錄錯誤，在沒有模式偵測的情況下繼續
- 查詢逾時：記錄警告，將 pattern_detected 設為 false
- 結果中的無效資料：跳過無效條目，處理有效條目

### Alert Logger 層

**資料庫寫入錯誤：**
- 連線失敗：將錯誤記錄到 stderr，向呼叫者回傳成功
- 約束違規：記錄錯誤，向呼叫者回傳成功
- 磁碟已滿：記錄嚴重錯誤，向呼叫者回傳成功

**設計理由：** 記錄失敗不應阻止警報分類完成。主要功能是回傳分類分析；記錄是次要的。

### 資料庫初始化錯誤

**結構建立錯誤：**
- 檔案權限被拒絕：在啟動時引發例外
- 無效的 SQL：在啟動時引發例外
- 磁碟已滿：在啟動時引發例外

**設計理由：** 資料庫初始化發生在啟動時。如果失敗，應用程式不應啟動。

## 測試策略

測試策略專注於確保系統核心功能的正確性和可靠性。

### 單元測試

**框架：** pytest

**重點領域：**
- 展示正確行為的特定範例
- 邊緣案例（空輸入、邊界條件）
- 具有特定錯誤訊息的錯誤條件
- 元件之間的整合點
- 資料庫結構驗證

**測試組織：**
```python
# tests/unit/test_api_endpoints.py
# tests/unit/test_ai_classifier.py
# tests/unit/test_pattern_detector.py
# tests/unit/test_alert_logger.py
# tests/unit/test_data_models.py
```

**單元測試範例：**

```python
def test_endpoint_exists():
    """驗證 /api/v1/triage 端點可存取。"""
    response = client.post("/api/v1/triage", json={})
    assert response.status_code != 404

def test_empty_alert_rejected():
    """空的 raw_data 應該被拒絕。"""
    response = client.post(
        "/api/v1/triage",
        json={"raw_data": ""}
    )
    assert response.status_code == 422

def test_database_schema_columns():
    """驗證 triage_logs 資料表中存在所有必要欄位。"""
    conn = sqlite3.connect("test.db")
    cursor = conn.execute("PRAGMA table_info(triage_logs)")
    columns = {row[1] for row in cursor.fetchall()}
    
    required = {
        "request_id", "timestamp", "raw_input", "severity",
        "threat_classification", "recommended_action", 
        "summary", "pattern_detected", "pattern_count"
    }
    assert required.issubset(columns)

def test_timestamp_index_exists():
    """驗證 timestamp 欄位上的索引。"""
    conn = sqlite3.connect("test.db")
    cursor = conn.execute("PRAGMA index_list(triage_logs)")
    indexes = {row[1] for row in cursor.fetchall()}
    assert "idx_timestamp" in indexes
```

### 整合測試

**範圍：** 使用模擬外部依賴的端到端流程

**關鍵場景：**
- 使用模擬 OpenAI API 的完整分類流程

**模擬策略：**
- 使用 `responses` 函式庫模擬 OpenAI API 回應
- 使用記憶體內 SQLite 資料庫進行測試

