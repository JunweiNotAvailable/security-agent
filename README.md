# AI 安全警報分類系統

使用 OpenAI GPT-4o-mini 模型的自動化安全警報分類系統。系統提供 REST API 端點，接受 JSON 或純文字格式的安全警報，並回傳包含嚴重程度評估、威脅分類、建議行動和模式偵測的結構化分析。

## 功能特色

- **REST API 整合**：單一端點 `/api/v1/triage` 便於整合
- **AI 驅動分類**：使用 OpenAI GPT-4o-mini 進行智慧威脅分析
- **模式偵測**：在可配置的時間視窗內識別重複的警報類型
- **完整記錄**：所有操作記錄到 SQLite 資料庫以供稽核追蹤
- **彈性輸入**：接受 JSON 和純文字警報格式
- **類型安全**：所有資料結構完整的 Pydantic 驗證

## 快速開始

### 先決條件

- Python 3.8+
- OpenAI API 金鑰

### 安裝

1. 複製儲存庫：
```bash
git clone <repository-url>
cd ai-security-alert-triage
```

2. 安裝依賴項：
```bash
pip install -r requirements.txt
```

3. 設定環境變數：
```bash
cp .env.example .env
# 編輯 .env 並新增您的 OpenAI API 金鑰
```

4. 執行應用程式：
```bash
python run.py
```

API 將在 `http://localhost:8000` 提供服務

## 配置

設定以下環境變數（或使用 `.env` 檔案）：

| 變數 | 說明 | 預設值 |
|----------|-------------|---------|
| `OPENAI_API_KEY` | 您的 OpenAI API 金鑰 | **必填** |
| `DATABASE_PATH` | SQLite 資料庫檔案路徑 | `triage_logs.db` |
| `PATTERN_DETECTION_WINDOW_HOURS` | 模式偵測回溯時數 | `24` |
| `PATTERN_DETECTION_THRESHOLD` | 標記模式的最少出現次數 | `3` |
| `OPENAI_MODEL` | 使用的 OpenAI 模型 | `gpt-4o-mini` |

## API 使用方式

### 端點

`POST /api/v1/triage`

### 請求格式

**JSON 格式：**
```bash
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: application/json" \
  -d '{
    "raw_data": "來自 IP 192.168.1.100 的登入失敗嘗試",
    "metadata": {"ip": "192.168.1.100", "user": "admin"},
    "source": "auth_system"
  }'
```

**純文字格式：**
```bash
curl -X POST http://localhost:8000/api/v1/triage \
  -H "Content-Type: text/plain" \
  -d "偵測到可疑檔案：C:\Users\admin\Downloads 中的 malware.exe"
```

### 回應格式

```json
{
  "severity": "high",
  "threat_classification": "brute_force_attack",
  "recommended_action": "封鎖 IP 位址並重設使用者密碼",
  "summary": "偵測到來自單一 IP 的多次登入失敗嘗試",
  "pattern_detected": true,
  "pattern_count": 5,
  "pattern_timestamps": [
    "2024-01-15T10:30:00Z",
    "2024-01-15T11:45:00Z"
  ]
}
```

### 回應欄位

- `severity`：警報嚴重程度（`critical`、`high`、`medium`、`low`）
- `threat_classification`：識別出的安全威脅類型
- `recommended_action`：建議的具體回應行動
- `summary`：威脅的人類可讀分析
- `pattern_detected`：指示是否發現重複模式的布林旗標
- `pattern_count`：偵測視窗內相似警報的數量（如果偵測到模式）
- `pattern_timestamps`：先前匹配警報的時間戳記（如果偵測到模式）

### 狀態碼

- `200`：成功的分類分析
- `400`：無效的輸入格式（格式錯誤的 JSON、不支援的內容類型）
- `422`：輸入驗證失敗（缺少必填欄位、無效的資料類型）
- `503`：AI 服務無法使用（OpenAI API 問題）
- `500`：內部伺服器錯誤

## 測試

執行測試套件：
```bash
pytest tests/
```

執行並產生覆蓋率報告：
```bash
pytest tests/ --cov=app --cov-report=html
```

## 資料庫結構

系統使用 SQLite，結構如下：

```sql
CREATE TABLE triage_logs (
    request_id TEXT PRIMARY KEY,
    timestamp REAL NOT NULL,
    raw_input TEXT NOT NULL,
    severity TEXT NOT NULL,
    threat_classification TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    summary TEXT NOT NULL,
    pattern_detected INTEGER NOT NULL,
    pattern_count INTEGER
);
```

在 `timestamp` 和 `threat_classification` 上建立索引以進行高效的模式偵測查詢。

## 架構

系統由五個主要元件組成：

1. **Alert_Ingestion_API**：處理 HTTP 請求的 FastAPI 端點
2. **AI_Classifier**：OpenAI API 整合以進行威脅分析
3. **Pattern_Detector**：識別重複的警報模式
4. **Alert_Logger**：將所有操作持久化到 SQLite 資料庫
5. **Configuration Manager**：管理環境變數和設定

## 疑難排解

### 常見問題

**「必要的環境變數 OPENAI_API_KEY 未設定」**
- 確保您已設定 `OPENAI_API_KEY` 環境變數
- 檢查您的 `.env` 檔案是否在專案根目錄中

**「AI 分類服務目前無法使用」**
- 驗證您的 OpenAI API 金鑰是否有效且有足夠的額度
- 檢查您的網路連線
- 確保 OpenAI API 沒有發生中斷

**「資料庫初始化失敗」**
- 檢查建立資料庫的目錄的檔案權限
- 確保有足夠的磁碟空間
- 驗證 `DATABASE_PATH` 是可寫入的

### 記錄

應用程式預設以 INFO 層級記錄到 stdout。記錄的關鍵事件包括：
- 配置驗證
- 資料庫初始化
- 成功的分類操作
- AI 分類錯誤
- 模式偵測結果

### 健康檢查

檢查服務是否正在執行：
```bash
curl http://localhost:8000/health
```

預期回應：
```json
{"status": "healthy"}
```

## 開發

### 專案結構

```
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 應用程式
│   ├── models.py            # Pydantic 資料模型
│   ├── config.py            # 配置管理
│   ├── database.py          # 資料庫初始化
│   ├── logger.py            # 警報記錄功能
│   ├── ai_classifier.py     # OpenAI API 整合
│   └── pattern_detector.py  # 模式偵測邏輯
├── tests/
│   └── __init__.py
├── requirements.txt
├── .env.example
├── run.py                   # 應用程式進入點
└── README.md
```

### 新增新功能

1. 更新 `models.py` 中的相應 Pydantic 模型
2. 修改相關的元件類別
3. 如需要，更新 `main.py` 中的 API 端點
4. 為新功能新增測試
5. 使用新的配置選項或 API 變更更新此 README

## 授權

此專案是漢昕科技業務持續運算系統（BCCS）架構的一部分。