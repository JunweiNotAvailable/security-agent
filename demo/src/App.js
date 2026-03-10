import React, { useState, useEffect, useRef } from 'react';

// 預設警報範例
const SAMPLE_ALERTS = [
  {
    id: 1,
    name: "SSH 暴力破解攻擊",
    raw_data: `[2024-01-15 03:47:22] 警報：偵測到多次 SSH 登入失敗嘗試
來源 IP：192.168.1.105 → 目標：prod-server-01
失敗嘗試：3 分鐘內 47 次
嘗試的使用者帳號：root、admin、ubuntu、deploy`,
    metadata: {
      source_ip: "192.168.1.105",
      target: "prod-server-01",
      failed_attempts: 47,
      duration_minutes: 3
    },
    source: "ssh_monitor"
  },
  {
    id: 2,
    name: "內部威脅 / 資料外洩",
    raw_data: `[2024-01-15 09:12:05] 警報：偵測到異常資料外洩模式
使用者：finance_user_03 | 部門：財務
從 /confidential/payroll/ 下載 2.3GB
目的地：外部 USB 裝置
非正常工作時間（晚上 9 點）`,
    metadata: {
      user: "finance_user_03",
      department: "Finance",
      data_size_gb: 2.3,
      destination: "USB",
      time: "21:00"
    },
    source: "dlp_system"
  },
  {
    id: 3,
    name: "重複攻擊（第 3 次）",
    raw_data: `[2024-01-15 14:33:18] 警報：SSH 暴力破解攻擊
來源 IP：203.0.113.42 → 目標：prod-server-01
失敗嘗試：2 分鐘內 31 次
嘗試的使用者帳號：root、admin、deploy
（24 小時內此類型的第 3 次警報）`,
    metadata: {
      source_ip: "203.0.113.42",
      target: "prod-server-01",
      failed_attempts: 31,
      duration_minutes: 2,
      alert_count_24h: 3
    },
    source: "ssh_monitor"
  }
];

const SeverityBadge = ({ level }) => {
  const colors = {
    critical: { bg: "#FF2D2D22", border: "#FF2D2D", text: "#FF6B6B" },
    high: { bg: "#FF8C0022", border: "#FF8C00", text: "#FFB347" },
    medium: { bg: "#FFD70022", border: "#FFD700", text: "#FFE44D" },
    low: { bg: "#00FF8822", border: "#00FF88", text: "#66FFB2" }
  };
  const c = colors[level?.toLowerCase()] || colors.low;
  return (
    <span style={{
      background: c.bg, border: `1px solid ${c.border}`, color: c.text,
      padding: "2px 10px", borderRadius: "4px", fontSize: "11px",
      fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase"
    }}>
      {level}
    </span>
  );
};

const TypewriterText = ({ text, speed = 18, onDone }) => {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    setDisplayed("");
    setDone(false);
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(interval);
        setDone(true);
        onDone?.();
      }
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed, onDone]);

  return (
    <span>
      {displayed}
      {!done && <span style={{ opacity: 0.6, animation: "blink 0.8s infinite" }}>|</span>}
    </span>
  );
};
const ManualPanel = ({ alert, running, onDone, manualTime = 8000 }) => {
  const [stepIndex, setStepIndex] = useState(-1);
  const [showResult, setShowResult] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef(null);

  const steps = [
    "正在讀取日誌條目...",
    "在 Google 搜尋威脅指標...",
    "檢查 IP 是內部還是外部...",
    "在筆記應用程式中撰寫事件摘要...",
    "手動決定嚴重程度...",
    "貼到工單系統..."
  ];

  useEffect(() => {
    if (!running) {
      setStepIndex(-1);
      setShowResult(false);
      setElapsed(0);
      return;
    }
    setStepIndex(0);
    setShowResult(false);
    setElapsed(0);
    timerRef.current = setInterval(() => setElapsed(e => e + 100), 100);
    return () => clearInterval(timerRef.current);
  }, [running, alert]);

  useEffect(() => {
    if (stepIndex < 0 || !running) return;
    if (stepIndex < steps.length) {
      const t = setTimeout(() => setStepIndex(s => s + 1), manualTime / steps.length);
      return () => clearTimeout(t);
    } else {
      clearInterval(timerRef.current);
      setShowResult(true);
      onDone?.();
    }
  }, [stepIndex, running, manualTime, onDone, steps.length]);

  return (
    <div style={{ flex: 1, background: "#0D0D0D", border: "1px solid #1E1E1E", borderRadius: "8px", padding: "20px", minHeight: 340 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <span style={{ color: "#666", fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase" }}>
          無系統 — 人工分析師
        </span>
        {running && !showResult && (
          <span style={{ color: "#FF8C00", fontSize: 11, fontFamily: "monospace" }}>
            ⏱ {(elapsed / 1000).toFixed(1)}秒 已耗時
          </span>
        )}
        {showResult && (
          <span style={{ color: "#FF4444", fontSize: 11, fontFamily: "monospace" }}>
            ⏱ {(manualTime / 1000).toFixed(1)}秒 總計
          </span>
        )}
      </div>

      {stepIndex >= 0 && (
        <div style={{ marginBottom: 16 }}>
          {steps.slice(0, stepIndex).map((step, i) => (
            <div key={i} style={{ color: "#444", fontSize: 12, fontFamily: "monospace", padding: "4px 0", display: "flex", gap: 8 }}>
              <span style={{ color: "#333" }}>✓</span> {step}
            </div>
          ))}
          {stepIndex < steps.length && (
            <div style={{ color: "#888", fontSize: 12, fontFamily: "monospace", padding: "4px 0", display: "flex", gap: 8 }}>
              <span style={{ color: "#FF8C00", animation: "spin 1s linear infinite", display: "inline-block" }}>◌</span>
              {steps[stepIndex]}
            </div>
          )}
        </div>
      )}

      {showResult && (
        <div style={{ background: "#111", border: "1px solid #2A2A2A", borderRadius: 6, padding: 14, marginTop: 8 }}>
          <div style={{ marginBottom: 8 }}>
            <SeverityBadge level="high" />
          </div>
          <div style={{ color: "#666", fontSize: 11, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            建議行動
          </div>
          <div style={{ color: "#888", fontSize: 12, marginBottom: 10 }}>
            可能要封鎖 IP？跟團隊確認一下
          </div>
          <div style={{ color: "#666", fontSize: 11, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            摘要
          </div>
          <div style={{ color: "#888", fontSize: 12, fontStyle: "italic" }}>
            SSH 攻擊，很多嘗試，可能很糟
          </div>
          <div style={{ marginTop: 12, padding: "8px 12px", background: "#1A0000", border: "1px solid #3A0000", borderRadius: 4, color: "#FF4444", fontSize: 11 }}>
            ⚠ 輸出模糊。無模式偵測。無稽核軌跡。依賴分析師記憶。
          </div>
        </div>
      )}

      {!running && stepIndex < 0 && (
        <div style={{ color: "#333", fontSize: 12, fontFamily: "monospace", paddingTop: 20 }}>
          等待警報中...
        </div>
      )}
    </div>
  );
};
const AIPanel = ({ alert, running, startDelay = 0, result, loading, error }) => {
  const [phase, setPhase] = useState("idle");
  const [showResult, setShowResult] = useState(false);

  useEffect(() => {
    if (!running) {
      setPhase("idle");
      setShowResult(false);
      return;
    }
    const t1 = setTimeout(() => setPhase("processing"), startDelay);
    return () => clearTimeout(t1);
  }, [running, alert, startDelay]);

  useEffect(() => {
    if (result && !loading) {
      setPhase("done");
      setShowResult(true);
    }
  }, [result, loading]);

  return (
    <div style={{
      flex: 1, background: "#0A0F0A",
      border: `1px solid ${phase === "done" ? "#00FF8833" : "#1A2A1A"}`,
      borderRadius: "8px", padding: "20px", minHeight: 340,
      transition: "border-color 0.4s"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <span style={{ color: "#00FF8888", fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase" }}>
          有系統 — AI 分類
        </span>
        {phase === "processing" && (
          <span style={{ color: "#00FF88", fontSize: 11, fontFamily: "monospace", animation: "pulse 0.8s infinite" }}>
            ⚡ 處理中...
          </span>
        )}
        {phase === "done" && result && (
          <span style={{ color: "#00FF88", fontSize: 11, fontFamily: "monospace" }}>
            ⚡ 完成
          </span>
        )}
      </div>

      {phase === "processing" && (
        <div style={{ padding: "20px 0" }}>
          {["解析警報結構...", "傳送至 AI 分類器...", "執行模式偵測..."].map((s, i) => (
            <div key={i} style={{
              color: "#00FF8866", fontSize: 12, fontFamily: "monospace",
              padding: "4px 0", display: "flex", gap: 8,
              animation: `fadeIn 0.3s ${i * 0.2}s both`
            }}>
              <span>▸</span>{s}
            </div>
          ))}
        </div>
      )}

      {error && (
        <div style={{ padding: "20px", background: "#1A0000", border: "1px solid #3A0000", borderRadius: 6, color: "#FF6666" }}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>❌ 錯誤</div>
          <div style={{ fontSize: 12 }}>{error}</div>
        </div>
      )}
      {showResult && result && !error && (
        <div style={{ background: "#0A1A0A", border: "1px solid #1A3A1A", borderRadius: 6, padding: 14 }}>
          <div style={{ display: "flex", gap: 8, marginBottom: 10, alignItems: "center" }}>
            <SeverityBadge level={result.severity} />
            {result.pattern_detected && (
              <span style={{
                background: "#FF000022", border: "1px solid #FF0000",
                color: "#FF6666", padding: "2px 10px", borderRadius: "4px",
                fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
                animation: "pulse 1s infinite"
              }}>
                🔺 已升級 — {result.pattern_count} 次於 24 小時內
              </span>
            )}
          </div>

          <div style={{ color: "#00FF8866", fontSize: 11, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            威脅分類
          </div>
          <div style={{ color: "#00FF88", fontSize: 13, fontWeight: 600, marginBottom: 10 }}>
            <TypewriterText text={result.threat_classification} speed={25} />
          </div>

          <div style={{ color: "#00FF8866", fontSize: 11, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            建議行動
          </div>
          <div style={{ color: "#88CC88", fontSize: 12, marginBottom: 10, lineHeight: 1.6 }}>
            <TypewriterText text={result.recommended_action} speed={12} />
          </div>

          <div style={{ color: "#00FF8866", fontSize: 11, marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            摘要
          </div>
          <div style={{ color: "#668866", fontSize: 12, fontStyle: "italic", lineHeight: 1.6 }}>
            <TypewriterText text={result.summary} speed={10} />
          </div>

          <div style={{ marginTop: 12, padding: "8px 12px", background: "#001A00", border: "1px solid #003A00", borderRadius: 4, color: "#00FF88", fontSize: 11 }}>
            ✓ 結構化 JSON 輸出 · 已記錄時間戳記 · 模式偵測啟用 · API 就緒
          </div>
        </div>
      )}

      {phase === "idle" && (
        <div style={{ color: "#1A3A1A", fontSize: 12, fontFamily: "monospace", paddingTop: 20 }}>
          等待警報中...
        </div>
      )}
    </div>
  );
};
function App() {
  const [selectedAlert, setSelectedAlert] = useState(0);
  const [running, setRunning] = useState(false);
  const [manualDone, setManualDone] = useState(false);
  const [aiResult, setAiResult] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);
  const [startTime, setStartTime] = useState(null);

  const alert = SAMPLE_ALERTS[selectedAlert];

  const runDemo = async () => {
    setRunning(false);
    setManualDone(false);
    setAiResult(null);
    setAiError(null);
    setAiLoading(false);

    setTimeout(async () => {
      setRunning(true);
      setAiLoading(true);
      setStartTime(Date.now());

      try {
        const response = await fetch('/api/v1/triage', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            raw_data: alert.raw_data,
            metadata: alert.metadata,
            source: alert.source
          })
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail?.detail || '分類失敗');
        }

        const data = await response.json();
        setAiResult(data);
        setAiError(null);
      } catch (error) {
        console.error('API 錯誤:', error);
        setAiError(error.message || '無法連接到 API');
        setAiResult(null);
      } finally {
        setAiLoading(false);
      }
    }, 100);
  };

  const getTimeSaved = () => {
    if (!aiResult || !startTime) return 0;
    const aiTime = (Date.now() - startTime) / 1000;
    const manualTime = 8;
    return Math.max(0, manualTime - aiTime).toFixed(1);
  };
  return (
    <div style={{
      background: "#080808", minHeight: "100vh", color: "#CCC",
      fontFamily: "'Noto Sans TC', 'IBM Plex Mono', monospace",
      padding: "32px 24px"
    }}>
      {/* 標題 */}
      <div style={{ marginBottom: 32, borderBottom: "1px solid #1A1A1A", paddingBottom: 24 }}>
        <div style={{ color: "#00FF88", fontSize: 11, letterSpacing: "0.15em", marginBottom: 6 }}>
          瀚鑫科技 // 系統展示
        </div>
        <div style={{ fontSize: 22, fontWeight: 700, color: "#EEE", letterSpacing: "-0.02em" }}>
          AI 安全警報分類系統
        </div>
        <div style={{ color: "#555", fontSize: 12, marginTop: 6 }}>
          人工分析師回應 vs. AI 驅動的自動化分類
        </div>
      </div>

      {/* 警報選擇器 */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ color: "#555", fontSize: 11, letterSpacing: "0.1em", marginBottom: 10, textTransform: "uppercase" }}>
          選擇情境
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {SAMPLE_ALERTS.map((a, i) => (
            <button
              key={i}
              onClick={() => {
                setSelectedAlert(i);
                setRunning(false);
                setManualDone(false);
                setAiResult(null);
                setAiError(null);
              }}
              style={{
                background: selectedAlert === i ? "#00FF8811" : "#111",
                border: `1px solid ${selectedAlert === i ? "#00FF88" : "#2A2A2A"}`,
                color: selectedAlert === i ? "#00FF88" : "#666",
                padding: "8px 16px", borderRadius: "4px", cursor: "pointer",
                fontSize: 11, fontFamily: "inherit", letterSpacing: "0.05em",
                transition: "all 0.2s"
              }}
            >
              {String(i + 1).padStart(2, '0')} — {a.name}
            </button>
          ))}
        </div>
      </div>
      {/* 原始警報 */}
      <div style={{ background: "#0D0D0D", border: "1px solid #1E1E1E", borderRadius: "8px", padding: "16px 20px", marginBottom: 20 }}>
        <div style={{ color: "#555", fontSize: 11, letterSpacing: "0.1em", marginBottom: 10, textTransform: "uppercase" }}>
          傳入警報
        </div>
        <pre style={{ color: "#FFA500", fontSize: 12, margin: 0, lineHeight: 1.8, whiteSpace: "pre-wrap" }}>
          {alert.raw_data}
        </pre>
      </div>

      {/* 執行按鈕 */}
      <div style={{ marginBottom: 20, display: "flex", alignItems: "center", gap: 16 }}>
        <button
          onClick={runDemo}
          disabled={running}
          style={{
            background: running ? "#001A00" : "#00FF88",
            color: running ? "#00FF88" : "#000",
            border: `1px solid ${running ? "#00FF88" : "#00FF88"}`,
            padding: "10px 28px", borderRadius: "4px",
            cursor: running ? "not-allowed" : "pointer",
            fontSize: 12, fontFamily: "inherit", fontWeight: 700,
            letterSpacing: "0.08em", transition: "all 0.2s"
          }}
        >
          {running ? "◉ 執行比較中..." : "▶ 執行比較"}
        </button>
        {manualDone && !running && (
          <span style={{ color: "#555", fontSize: 11 }}>
            展示完成 — 試試其他情境或再次執行
          </span>
        )}
      </div>

      {/* 並排比較 */}
      <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
        <ManualPanel alert={alert} running={running} onDone={() => setManualDone(true)} />
        <AIPanel alert={alert} running={running} startDelay={200} result={aiResult} loading={aiLoading} error={aiError} />
      </div>
      {/* 底部統計 */}
      {manualDone && aiResult && (
        <div style={{ display: "flex", gap: 12, animation: "slideUp 0.4s ease" }}>
          {[
            { label: "節省時間", value: `~${getTimeSaved()}秒 每個警報`, color: "#00FF88" },
            { label: "輸出品質", value: "結構化 vs 自由格式", color: "#00FF88" },
            {
              label: "模式偵測",
              value: aiResult.pattern_detected ? `已觸發 🔺 (${aiResult.pattern_count}次)` : "啟用中",
              color: aiResult.pattern_detected ? "#FF4444" : "#00FF88"
            },
            { label: "稽核軌跡", value: "自動記錄", color: "#00FF88" },
          ].map((s, i) => (
            <div key={i} style={{
              flex: 1, background: "#0D0D0D", border: "1px solid #1A2A1A",
              borderRadius: 6, padding: "12px 16px"
            }}>
              <div style={{ color: "#555", fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 4 }}>
                {s.label}
              </div>
              <div style={{ color: s.color, fontSize: 13, fontWeight: 600 }}>
                {s.value}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;