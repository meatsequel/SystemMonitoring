"""
Tests the report.py functions
"""
import pytest
from unittest.mock import patch
from unittest import mock

from report import CpuReport, MemoryReport, DiskReport, Report, MetricStats, _read_log, _compute_stats, _check_breaches, get_report

# -----------------------------------
# Helper Functions
# -----------------------------------

def make_cpu_report():
    return CpuReport(
        aggregate=MetricStats(min=2.11, avg=2.56, max=3.01),
        per_core=[
            MetricStats(min=7.5, avg=9.05, max=10.6),
            MetricStats(min=0.0, avg=0.0, max=0.0),
        ]
    )

def make_memory_report():
    return MemoryReport(percent=MetricStats(min=43.4, avg=43.4, max=43.4))

def make_disk_reports():
    return [
        DiskReport(device="C:", mountpoint="C:", percent=MetricStats(min=82.1, avg=82.1, max=82.1)),
        DiskReport(device="D:", mountpoint="D:", percent=MetricStats(min=7.0, avg=7.0, max=7.0)),
        DiskReport(device="E:", mountpoint="E:", percent=MetricStats(min=91.9, avg=91.9, max=91.9)),
        DiskReport(device="F:", mountpoint="F:", percent=MetricStats(min=34.2, avg=34.2, max=34.2)),
    ]

def make_log_lines():
    return [
        '{"timestamp": "2026-03-19 11:34:55", "cpu": {"aggregate_percent": 3.00625, "per_core_percent": [10.6, 0.0, 4.7, 4.6, 0.0, 0.0, 0.0, 1.6, 0.0, 3.1, 7.8, 1.6, 4.7, 0.0, 7.8, 1.6]}, "memory": {"total_bytes": 34257379328, "available_bytes": 19395764224, "used_bytes": 14861615104, "free_bytes": 19395764224, "percent": 43.4}, "disks": [{"device": "C:", "mountpoint": "C:", "fstype": "NTFS", "total_bytes": 499158196224, "used_bytes": 409774686208, "free_bytes": 89383510016, "percent": 82.1}, {"device": "D:", "mountpoint": "D:", "fstype": "NTFS", "total_bytes": 524283904, "used_bytes": 36532224, "free_bytes": 487751680, "percent": 7.0}, {"device": "E:", "mountpoint": "E:", "fstype": "NTFS", "total_bytes": 1999323250688, "used_bytes": 1837847474176, "free_bytes": 161475776512, "percent": 91.9}, {"device": "F:", "mountpoint": "F:", "fstype": "NTFS", "total_bytes": 1000186310656, "used_bytes": 342249750528, "free_bytes": 657936560128, "percent": 34.2}], "errors": []}',
        '{"timestamp": "2026-03-19 11:34:57", "cpu": {"aggregate_percent": 2.1125000000000003, "per_core_percent": [7.5, 0.0, 1.5, 1.5, 0.0, 0.0, 0.0, 3.0, 3.1, 0.0, 6.2, 0.0, 1.6, 1.6, 6.2, 1.6]}, "memory": {"total_bytes": 34257379328, "available_bytes": 19387047936, "used_bytes": 14870331392, "free_bytes": 19387047936, "percent": 43.4}, "disks": [{"device": "C:", "mountpoint": "C:", "fstype": "NTFS", "total_bytes": 499158196224, "used_bytes": 409774694400, "free_bytes": 89383501824, "percent": 82.1}, {"device": "D:", "mountpoint": "D:", "fstype": "NTFS", "total_bytes": 524283904, "used_bytes": 36532224, "free_bytes": 487751680, "percent": 7.0}, {"device": "E:", "mountpoint": "E:", "fstype": "NTFS", "total_bytes": 1999323250688, "used_bytes": 1837847474176, "free_bytes": 161475776512, "percent": 91.9}, {"device": "F:", "mountpoint": "F:", "fstype": "NTFS", "total_bytes": 1000186310656, "used_bytes": 342249750528, "free_bytes": 657936560128, "percent": 34.2}], "errors": []}',
    ]

# -----------------------------------
# Read Log Tests
# -----------------------------------

def test_read_log():
    lines = [make_log_lines()[0]]
    with patch("builtins.open", mock.mock_open(read_data="\n".join(lines))):
        entries = _read_log("test.jsonl", "2026-03-19")

    assert len(entries) == 1
    assert isinstance(entries, list)
    assert entries[0]["timestamp"] == "2026-03-19 11:34:55"
    assert entries[0]["cpu"]["aggregate_percent"] == 3.00625

def test_read_log_multi_line():
    with patch("builtins.open", mock.mock_open(read_data="\n".join(make_log_lines()))):
        entries = _read_log("test.jsonl", "2026-03-19")

    assert len(entries) == 2
    assert isinstance(entries, list)
    assert entries[0]["timestamp"] == "2026-03-19 11:34:55"
    assert entries[0]["cpu"]["aggregate_percent"] == 3.00625
    assert entries[1]["timestamp"] == "2026-03-19 11:34:57"
    assert entries[1]["cpu"]["aggregate_percent"] == pytest.approx(2.1125)

def test_read_log_error():
    with patch("builtins.open") as mock_file:
        mock_file.side_effect = OSError()
        entries = _read_log("test.jsonl", "2026-03-19")

    assert isinstance(entries, str)
    assert entries == "Could not read log file at test.jsonl! Error "

# -----------------------------------
# Compute Stats Tests
# -----------------------------------

def test_compute_stats():
    result = _compute_stats([1.1, 2.2, 3.3, 4.4, 5.5, 6.6])

    assert result.min == 1.1
    assert result.max == 6.6
    assert result.avg == 3.85

# -----------------------------------
# Check Breaches Tests
# -----------------------------------

def test_check_breaches_no_thresholds():
    breaches = _check_breaches(make_cpu_report(), make_memory_report(), make_disk_reports(),
                               cpu_threshold=None, mem_threshold=None, disk_threshold=None)

    assert breaches == []

def test_check_breaches_breach_detected():
    breaches = _check_breaches(make_cpu_report(), make_memory_report(), make_disk_reports(),
                               cpu_threshold=3.0, mem_threshold=43.0, disk_threshold=90.0)

    metrics = [b.metric for b in breaches]
    assert "CPU Aggregate" in metrics
    assert "Memory" in metrics
    assert "Disk E:" in metrics

def test_check_breaches_no_breach():
    breaches = _check_breaches(make_cpu_report(), make_memory_report(), make_disk_reports(),
                               cpu_threshold=99.0, mem_threshold=99.0, disk_threshold=99.0)

    assert breaches == []

# -----------------------------------
# Get Report Tests
# -----------------------------------

def test_get_report():
    with patch("builtins.open", mock.mock_open(read_data="\n".join(make_log_lines()))):
        result = get_report("test.jsonl", "2026-03-19")

    assert isinstance(result, Report)
    assert result.date == "2026-03-19"
    assert result.num_snapshots == 2
    assert result.cpu.aggregate.min == round(2.1125000000000003, 2)
    assert result.cpu.aggregate.max == round(3.00625, 2)
    assert result.memory.percent.min == 43.4
    assert result.memory.percent.max == 43.4
    assert len(result.disks) == 4
    assert result.disks[0].mountpoint == "C:"
    assert result.disks[0].percent.max == 82.1
    assert result.breaches == []

def test_get_report_with_breaches():
    with patch("builtins.open", mock.mock_open(read_data="\n".join(make_log_lines()))):
        result = get_report("test.jsonl", "2026-03-19", cpu_threshold=3.0, mem_threshold=43.0, disk_threshold=90.0)

    assert isinstance(result, Report)
    metrics = [b.metric for b in result.breaches]
    assert "CPU Aggregate" in metrics
    assert "Memory" in metrics
    assert "Disk E:" in metrics

def test_get_report_no_entries():
    lines = [make_log_lines()[0].replace("2026-03-19", "2026-03-18")]
    with patch("builtins.open", mock.mock_open(read_data="\n".join(lines))):
        result = get_report("test.jsonl", "2026-03-19")

    assert isinstance(result, str)
    assert "No entries found" in result

def test_get_report_file_error():
    with patch("builtins.open") as mock_file:
        mock_file.side_effect = OSError()
        result = get_report("test.jsonl", "2026-03-19")

    assert isinstance(result, str)
    assert "Could not read log file" in result
