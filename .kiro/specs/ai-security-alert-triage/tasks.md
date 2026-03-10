# 實作計畫：AI 安全警報分類系統

## 概述

此實作計畫將 AI 安全警報分類系統分解為離散的編碼任務。系統是一個基於 Python 的 REST API，使用 FastAPI，整合 OpenAI API 以分類安全警報、偵測模式，並將所有操作記錄到 SQLite。

實作遵循由下而上的方法：從資料模型和資料庫設定開始，然後建構核心元件（AI 分類器、模式偵測器、記錄器），最後透過 FastAPI 端點將所有內容連接在一起。

## 任務

- [ ] 1. 設定專案結構和依賴項
  - 建立專案目錄結構（app/、tests/、config/）
  - 建立包含 FastAPI、Pydantic、OpenAI SDK、SQLite、pytest、hypothesis 的 requirements.txt
  - 建立配置範本的 .env.example 檔案
  - 設定基本的 FastAPI 應用程式骨架
  - _需求：7.6_

- [ ] 2. 實作資料模型和驗證結構
  - [ ] 2.1 為 SecurityAlert、TriageReport 和 AlertLogEntry 建立 Pydantic 模型
    - 定義包含 raw_data、metadata 和 source 欄位的 SecurityAlert
    - 定義包含 critical、high、medium、low 值的 SeverityLevel 列舉
    - 定義包含所有必填欄位和可選模式欄位的 TriageReport
    - 定義用於資料庫結構映射的 AlertLogEntry
    - 為所有模型新增 JSON 結構範例
    - _需求：6.1、6.2、6.3、6.5、6.6、3.2_

  - [ ]* 2.2 為資料模型驗證撰寫屬性測試
    - **屬性 14：必填欄位強制執行**
    - **屬性 15：類型強制執行**
    - **驗證：需求 6.5、6.6**

- [ ] 3. 實作資料庫層和 Alert_Logger 元件
  - [ ] 3.1 建立資料庫初始化模組
    - 撰寫建立 SQLite 資料庫檔案的函式
    - 定義包含所有必要欄位的結構（request_id、timestamp、raw_input、severity、threat_classification、recommended_action、summary、pattern_detected、pattern_count）
    - 在 timestamp 和 threat_classification 欄位上建立索引
    - 新增結構建立失敗的錯誤處理
    - _需求：8.1、8.2、8.3、8.4、8.5、8.6_

  - [ ]* 3.2 為資料庫結構撰寫單元測試
    - 測試資料庫檔案建立
    - 驗證所有欄位存在且類型正確
    - 驗證索引已建立
    - 測試結構建立的冪等性

  - [ ] 3.3 實作 Alert_Logger 類別
    - 撰寫 log_triage 方法以持久化請求和回應資料
    - 使用 UUID 生成唯一的 request_id
    - 儲存毫秒精度的時間戳記
    - 實作優雅的錯誤處理（記錄錯誤但不引發例外）
    - _需求：4.1、4.2、4.3、4.4、4.5、4.6、4.7_

  - [ ]* 3.4 為 Alert_Logger 撰寫屬性測試
    - **屬性 9：完整日誌持久化**
    - **屬性 10：請求-回應關聯**
    - **屬性 11：記錄韌性**
    - **驗證：需求 4.1、4.2、4.3、4.4、4.5、4.6、4.7**

- [ ] 4. 檢查點 - 驗證資料庫層
  - 確保所有測試通過，如有問題請詢問使用者。

- [ ] 5. 實作 Configuration Manager
  - [ ] 5.1 為環境變數建立 Config 類別
    - 從環境載入 OPENAI_API_KEY
    - 定義具有預設值的 DATABASE_PATH
    - 定義 PATTERN_DETECTION_WINDOW_HOURS（預設 24）
    - 定義 PATTERN_DETECTION_THRESHOLD（預設 3）
    - 定義 OPENAI_MODEL（預設 "gpt-4o-mini"）
    - 新增啟動時必要配置的驗證
    - _需求：2.2_

  - [ ]* 5.2 為配置撰寫單元測試
    - 測試環境變數載入
    - 測試預設值
    - 測試缺少必要配置的處理

- [ ] 6. 實作 AI_Classifier 元件
  - [ ] 6.1 建立具有 OpenAI 整合的 AIClassifier 類別
    - 實作 classify_alert 方法
    - 建構以安全為重點的系統提示詞
    - 使用 gpt-4o-mini 模型呼叫 OpenAI API
    - 解析 JSON 回應並提取所有必填欄位
    - 處理 API 錯誤（逾時、速率限制、無效回應）
    - 在 API 失敗時回傳 HTTP 503
    - _需求：2.1、2.2、2.3、2.4、2.5、2.6、2.7_

  - [ ]* 6.2 為 AI_Classifier 撰寫屬性測試
    - **屬性 4：OpenAI API 整合**
    - **屬性 5：完整回應解析**
    - **屬性 6：API 錯誤處理**
    - **驗證：需求 2.1、2.2、2.3、2.4、2.5、2.6、2.7**

  - [ ]* 6.3 為 AI_Classifier 撰寫單元測試
    - 使用模擬的 OpenAI API 回應進行測試
    - 測試網路失敗的錯誤處理
    - 測試回應解析邊緣案例
    - 測試無效 severity 值處理

- [ ] 7. 實作 Pattern_Detector 元件
  - [ ] 7.1 建立 PatternDetector 類別
    - 實作 detect_patterns 方法
    - 查詢資料庫中具有匹配 threat_classification 的警報
    - 將結果篩選至從當前時間戳記起的 24 小時視窗
    - 計算匹配的出現次數
    - 當計數 >= 3 時新增 pattern_detected 旗標
    - 在豐富化報告中包含 pattern_count 和 pattern_timestamps
    - 優雅地處理資料庫查詢錯誤
    - _需求：5.1、5.2、5.3、5.4、5.5、5.6_

  - [ ]* 7.2 為 Pattern_Detector 撰寫屬性測試
    - **屬性 12：模式偵測查詢**
    - **屬性 13：模式偵測閾值**
    - **驗證：需求 5.1、5.2、5.3、5.4、5.5、5.6**

  - [ ]* 7.3 為 Pattern_Detector 撰寫單元測試
    - 使用預先填充的資料庫進行測試
    - 測試 24 小時視窗邊界條件
    - 測試閾值邊緣案例（恰好 3 次出現）
    - 測試資料庫查詢錯誤處理

- [ ] 8. 檢查點 - 驗證核心元件
  - 確保所有測試通過，如有問題請詢問使用者。

- [ ] 9. 實作 Alert_Ingestion_API 端點
  - [ ] 9.1 在 /api/v1/triage 建立 FastAPI 端點
    - 定義具有 Request 參數的 POST 端點
    - 處理 Content-Type application/json 和 text/plain
    - 根據 Content-Type 標頭解析請求主體
    - 根據 SecurityAlert 結構驗證輸入
    - 協調對 AI_Classifier、Pattern_Detector、Alert_Logger 的呼叫
    - 成功時回傳 HTTP 200 並附上 TriageReport JSON
    - 對於無效的輸入格式回傳 HTTP 400
    - 對於結構驗證失敗回傳 HTTP 422
    - 對於 OpenAI API 錯誤回傳 HTTP 503
    - 以描述性訊息格式化錯誤回應
    - _需求：1.1、1.2、1.3、1.4、1.5、1.6、3.7、7.1、7.2、7.3、7.4、7.5_

  - [ ]* 9.2 為 API 端點撰寫屬性測試
    - **屬性 1：Content-Type 接受**
    - **屬性 2：輸入結構驗證**
    - **屬性 3：無效輸入拒絕**
    - **屬性 7：輸出結構驗證**
    - **屬性 8：成功回應格式**
    - **驗證：需求 1.1、1.2、1.3、1.4、1.5、1.6、3.2、3.3、3.4、3.5、3.6、3.7、7.2、7.3、7.4**

  - [ ]* 9.3 為 API 端點撰寫單元測試
    - 測試端點可存取性
    - 測試空警報拒絕
    - 測試格式錯誤的 JSON 處理
    - 測試純文字輸入解析
    - 測試錯誤回應格式

- [ ] 10. 實作應用程式啟動和初始化
  - [ ] 10.1 建立主應用程式進入點
    - 在啟動時初始化資料庫
    - 驗證配置
    - 建立 FastAPI 應用程式實例
    - 新增全域錯誤處理的例外處理器
    - _需求：8.6_

  - [ ]* 10.2 為啟動撰寫整合測試
    - 測試首次執行時的資料庫初始化
    - 測試配置驗證
    - 測試缺少 API 金鑰時的啟動

- [ ] 11. 為屬性測試新增自訂 Hypothesis 策略
  - [ ] 11.1 建立測試工具和生成器
    - 定義用於生成 SecurityAlert 實例的 security_alert_strategy
    - 定義用於生成有效嚴重程度的 severity_strategy
    - 定義用於模式偵測測試的 timestamp_strategy
    - 配置 Hypothesis 設定（最少 100 次迭代）
    - _需求：所有屬性測試_

- [ ] 12. 實作端到端整合測試
  - [ ]* 12.1 使用模擬的 OpenAI API 撰寫整合測試
    - 測試從請求到回應的完整分類流程
    - 使用預先填充的資料庫測試模式偵測
    - 測試並發請求處理
    - 測試錯誤恢復場景
    - _需求：所有需求_

- [ ] 13. 最終檢查點 - 完整系統驗證
  - 確保所有測試通過，如有問題請詢問使用者。

- [ ] 14. 新增文件和部署配置
  - [ ] 14.1 建立包含設定說明的 README
    - 記錄 API 端點使用方式
    - 提供請求和回應範例
    - 記錄環境變數
    - 新增疑難排解章節

  - [ ] 14.2 建立 Docker 配置（可選）
    - 撰寫用於容器化部署的 Dockerfile
    - 建立用於本地開發的 docker-compose.yml
    - 記錄 Docker 部署流程

## 注意事項

- 標記為 `*` 的任務是可選的，可以跳過以更快獲得 MVP
- 每個任務都參考特定需求以便追溯
- 屬性測試驗證設計文件中的通用正確性屬性
- 單元測試驗證特定範例和邊緣案例
- 實作使用 Python 搭配 FastAPI、Pydantic、OpenAI SDK 和 SQLite
- 所有資料庫操作使用 SQLite 的內建 Python 模組（sqlite3）
- 模式偵測查詢使用 timestamp 和 threat_classification 上的索引進行最佳化
- 錯誤處理遵循深度防禦：記錄失敗不會阻止分類完成
