# 需求文件

## 簡介

AI 安全警報分類系統是一個輕量級模組，使用 AI 自動化安全警報的分類與分析。系統透過 REST API 接收原始警報資料，經由 OpenAI API 以安全為重點的提示詞進行處理，並回傳包含嚴重程度、威脅分類和建議行動的結構化分析。所有互動都會記錄到本地資料庫，系統會偵測重複出現的警報類型模式，以標記潛在的系統性問題。

## 術語表

- **Alert_Ingestion_API**：從外部系統接收安全警報資料的 REST API 端點
- **AI_Classifier**：將警報資料傳送至 OpenAI API 並處理回應的元件
- **Triage_Report**：包含嚴重程度、分類、建議和摘要的結構化 JSON 輸出
- **Alert_Logger**：將請求和回應資料持久化到資料庫的元件
- **Pattern_Detector**：在時間視窗內識別重複警報類型的元件
- **Alert_Type**：由 AI_Classifier 指派的分類類別，用於分組相似警報
- **Security_Alert**：提交到系統進行分析的原始警報資料

## 需求

### 需求 1：接受警報輸入

**使用者故事：** 作為安全維運工程師，我想透過 REST API 提交安全警報，以便將分類系統整合到我現有的工作流程中。

#### 驗收標準

1. Alert_Ingestion_API 應接受包含警報資料的 JSON 格式 POST 請求
2. Alert_Ingestion_API 應接受包含警報資料的純文字格式 POST 請求
3. 當收到有效的 JSON 請求時，Alert_Ingestion_API 應將其解析為 Security_Alert 物件
4. 當收到純文字請求時，Alert_Ingestion_API 應將其解析為 Security_Alert 物件
5. 當收到無效資料格式的請求時，Alert_Ingestion_API 應回傳 HTTP 400 並附上描述性錯誤訊息
6. Alert_Ingestion_API 應在處理前根據 Pydantic schema 驗證輸入資料

### 需求 2：AI 驅動的警報分類

**使用者故事：** 作為安全分析師，我想要警報由 AI 自動分類，以便我能優先處理回應工作。

#### 驗收標準

1. 當收到有效的 Security_Alert 時，AI_Classifier 應將警報資料以安全為重點的系統提示詞傳送至 OpenAI API
2. AI_Classifier 應使用 gpt-4o-mini 模型進行分類
3. 當 OpenAI API 回傳回應時，AI_Classifier 應從回應中提取嚴重程度
4. 當 OpenAI API 回傳回應時，AI_Classifier 應從回應中提取威脅分類
5. 當 OpenAI API 回傳回應時，AI_Classifier 應從回應中提取建議的回應行動
6. 當 OpenAI API 回傳回應時，AI_Classifier 應從回應中提取人類可讀的摘要
7. 如果 OpenAI API 呼叫失敗，則 AI_Classifier 應回傳 HTTP 503 並附上錯誤訊息

### 需求 3：結構化輸出生成

**使用者故事：** 作為安全維運工程師，我想要標準化的分類報告，以便我能以程式化方式處理結果。

#### 驗收標準

1. AI_Classifier 應以 JSON 格式回傳 Triage_Report
2. Triage_Report 應包含 severity 欄位，其值限定為 critical、high、medium 或 low
3. Triage_Report 應包含 threat_classification 欄位，內含 Alert_Type
4. Triage_Report 應包含 recommended_action 欄位，內含回應指引
5. Triage_Report 應包含 summary 欄位，內含人類可讀的分析
6. Triage_Report 在回傳前應根據 Pydantic schema 進行驗證
7. 當生成 Triage_Report 時，Alert_Ingestion_API 應回傳 HTTP 200 並附上 JSON 格式的報告

### 需求 4：請求與回應記錄

**使用者故事：** 作為安全稽核員，我想要記錄所有分類操作，以便我能檢視歷史決策和系統行為。

#### 驗收標準

1. 當收到 Security_Alert 時，Alert_Logger 應將請求資料持久化到 SQLite 資料庫
2. 當生成 Triage_Report 時，Alert_Logger 應將回應資料持久化到 SQLite 資料庫
3. Alert_Logger 應為每個日誌條目記錄毫秒精度的時間戳記
4. Alert_Logger 應使用唯一識別碼將每個請求與其對應的回應關聯
5. Alert_Logger 應在日誌條目中儲存原始警報輸入
6. Alert_Logger 應在日誌條目中儲存完整的 Triage_Report
7. 如果資料庫寫入失敗，則 Alert_Logger 應記錄錯誤但仍將 Triage_Report 回傳給呼叫者

### 需求 5：重複警報的模式偵測

**使用者故事：** 作為安全分析師，我想在相同警報類型重複出現時收到通知，以便我能識別系統性問題。

#### 驗收標準

1. 當生成 Triage_Report 時，Pattern_Detector 應查詢資料庫中過去 24 小時內具有相同 Alert_Type 的警報
2. 當匹配的 Alert_Type 條目數量達到 3 個或更多時，Pattern_Detector 應在 Triage_Report 中新增 pattern_detected 旗標
3. 當偵測到模式時，Pattern_Detector 應在 Triage_Report 中包含出現次數
4. 當偵測到模式時，Pattern_Detector 應在 Triage_Report 中包含先前出現的時間戳記
5. Pattern_Detector 應使用 threat_classification 欄位中的 Alert_Type 進行匹配
6. Pattern_Detector 應從當前請求時間戳記計算 24 小時視窗

### 需求 6：資料結構驗證

**使用者故事：** 作為與分類系統整合的開發者，我想要清楚的結構驗證，以便我能快速識別並修復整合問題。

#### 驗收標準

1. Alert_Ingestion_API 應為 Security_Alert 輸入定義 Pydantic 模型
2. Alert_Ingestion_API 應為 Triage_Report 輸出定義 Pydantic 模型
3. Alert_Logger 應為日誌條目結構定義 Pydantic 模型
4. 當輸入驗證失敗時，Alert_Ingestion_API 應回傳 HTTP 422 並附上欄位層級的錯誤詳情
5. Pydantic 模型應對所有關鍵資料元素強制執行必填欄位
6. Pydantic 模型應為所有欄位定義資料類型

### 需求 7：API 端點規格

**使用者故事：** 作為安全維運工程師，我想要定義明確的 API 端點，以便我能可靠地整合分類系統。

#### 驗收標準

1. Alert_Ingestion_API 應在 /api/v1/triage 公開 POST 端點
2. Alert_Ingestion_API 應接受 Content-Type application/json
3. Alert_Ingestion_API 應接受 Content-Type text/plain
4. 當處理成功完成時，Alert_Ingestion_API 應回傳 Content-Type application/json
5. Alert_Ingestion_API 應為所有回應情境包含適當的 HTTP 狀態碼
6. Alert_Ingestion_API 應使用 FastAPI 框架實作端點

### 需求 8：記錄用資料庫結構

**使用者故事：** 作為系統管理員，我想要簡單的資料庫結構，以便我能查詢和維護歷史日誌。

#### 驗收標準

1. Alert_Logger 應建立 SQLite 資料庫檔案以進行持久化儲存
2. Alert_Logger 應定義包含 request_id、timestamp、raw_input、severity、threat_classification、recommended_action、summary 和 pattern_detected 欄位的資料表
3. Alert_Logger 應使用 request_id 作為主鍵
4. Alert_Logger 應為 timestamp 欄位建立索引以進行高效的時間範圍查詢
5. Alert_Logger 應為 threat_classification 欄位建立索引以進行高效的模式偵測查詢
6. 當資料庫檔案不存在時，Alert_Logger 應使用所需的結構建立它

