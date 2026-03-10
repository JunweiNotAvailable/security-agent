"""
資料模型的單元測試
"""

import pytest
from datetime import datetime
from app.models import SecurityAlert, TriageReport, SeverityLevel, AlertLogEntry


def test_security_alert_valid():
    """測試有效資料的 SecurityAlert"""
    alert = SecurityAlert(
        raw_data="登入失敗嘗試",
        metadata={"ip": "192.168.1.1"},
        source="auth_system"
    )
    assert alert.raw_data == "登入失敗嘗試"
    assert alert.metadata["ip"] == "192.168.1.1"
    assert alert.source == "auth_system"


def test_security_alert_minimal():
    """測試最少必要資料的 SecurityAlert"""
    alert = SecurityAlert(raw_data="測試警報")
    assert alert.raw_data == "測試警報"
    assert alert.metadata is None
    assert alert.source is None


def test_security_alert_empty_raw_data():
    """測試 SecurityAlert 拒絕空的 raw_data"""
    with pytest.raises(ValueError):
        SecurityAlert(raw_data="")


def test_triage_report_valid():
    """測試有效資料的 TriageReport"""
    report = TriageReport(
        severity=SeverityLevel.HIGH,
        threat_classification="brute_force_attack",
        recommended_action="封鎖 IP 位址",
        summary="多次登入失敗嘗試"
    )
    assert report.severity == SeverityLevel.HIGH
    assert report.threat_classification == "brute_force_attack"
    assert report.pattern_detected is False
    assert report.pattern_count is None


def test_triage_report_with_pattern():
    """測試包含模式偵測的 TriageReport"""
    timestamps = [datetime.now(), datetime.now()]
    report = TriageReport(
        severity=SeverityLevel.CRITICAL,
        threat_classification="malware",
        recommended_action="隔離系統",
        summary="偵測到惡意軟體",
        pattern_detected=True,
        pattern_count=3,
        pattern_timestamps=timestamps
    )
    assert report.pattern_detected is True
    assert report.pattern_count == 3
    assert len(report.pattern_timestamps) == 2


def test_severity_levels():
    """測試所有嚴重程度都是有效的"""
    assert SeverityLevel.CRITICAL == "critical"
    assert SeverityLevel.HIGH == "high"
    assert SeverityLevel.MEDIUM == "medium"
    assert SeverityLevel.LOW == "low"


def test_alert_log_entry():
    """測試 AlertLogEntry 結構"""
    entry = AlertLogEntry(
        request_id="test-123",
        timestamp=datetime.now(),
        raw_input="測試警報",
        severity="high",
        threat_classification="test_threat",
        recommended_action="測試行動",
        summary="測試摘要",
        pattern_detected=False
    )
    assert entry.request_id == "test-123"
    assert entry.severity == "high"
    assert entry.pattern_detected is False
    assert entry.pattern_count is None