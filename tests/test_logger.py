"""
Tests the logger.py functions
"""
from unittest.mock import patch
import datetime as dt
import pytest
import json

from collector import CpuMetrics, MemoryMetrics, PartitionMetrics, Snapshot, NetworkMetrics
from logger import Logger

# -----------------------------------
# Helper Functions
# -----------------------------------

def read_lines(path):
    with open(path, "r") as fl:
        return fl.readlines()
    
def make_snapshot(disks=None):
    if disks is None:
        disks = [PartitionMetrics(device='C:\\', mountpoint='C:\\', fstype='NTFS', total_bytes=499158196224, used_bytes=384851550208, free_bytes=114306646016, percent=77.1)]
    return Snapshot(
        timestamp=dt.datetime(2026, 3, 17, 12, 0, 0, tzinfo=dt.timezone.utc),
        cpu=CpuMetrics(aggregate_percent=8.85, per_core_percent=[23.2, 1.6]),
        memory=MemoryMetrics(total_bytes=34257379328, available_bytes=19424673792, used_bytes=14832705536, free_bytes=19424673792, percent=43.3),
        disks=disks,
        errors=[],
        networks=[NetworkMetrics(interface="Ethernet", upload=141826714.54, download=390038572.01)]
    )

# -----------------------------------
# __init__ Tests
# -----------------------------------

def test_invalid_path(tmp_path):
    with pytest.raises(OSError):
        Logger(str(tmp_path / "nonexistent" / "test.jsonl"))

def test_path_is_directory(tmp_path):
    with pytest.raises(OSError):
        Logger(str(tmp_path))

def test_valid_path(tmp_path):
    log = Logger(str(tmp_path / "test.jsonl"))
    assert log.log_path == str(tmp_path / "test.jsonl")

# -----------------------------------
# Snapshot to Dict Tests
# -----------------------------------

def test_snapshot_2_dict(tmp_path):
    log = Logger(str(tmp_path / "test.jsonl"))
    snapshot = make_snapshot()
    result = log._snapshot_2_dict(snapshot)

    assert result["timestamp"] == "2026-03-17 12:00:00"
    assert result["cpu"]["aggregate_percent"] == 8.85
    assert result["memory"]["percent"] == 43.3
    assert len(result["disks"]) == 1
    assert len(result["errors"]) == 0
    assert len(result["networks"]) == 1
    assert result["networks"][0]["interface"] == "Ethernet"

def test_snapshot_2_dict_no_disks(tmp_path):
    log = Logger(str(tmp_path / "test.jsonl"))
    snapshot = make_snapshot(disks=[])
    result = log._snapshot_2_dict(snapshot)

    assert result["timestamp"] == "2026-03-17 12:00:00"
    assert result["cpu"]["aggregate_percent"] == 8.85
    assert result["memory"]["percent"] == 43.3
    assert len(result["disks"]) == 0
    assert len(result["errors"]) == 0

# -----------------------------------
# Log to File Tests
# -----------------------------------
    
def test_log_2_file(tmp_path):
    log = Logger(str(tmp_path / "test.jsonl"))
    snapshot_dict = log._snapshot_2_dict(make_snapshot())
    result = log._log_2_file(snapshot_dict)

    assert result is None

    file_lines = read_lines(str(tmp_path / "test.jsonl"))

    parsed = json.loads(file_lines[0])
    assert parsed["timestamp"] == "2026-03-17 12:00:00"
    assert parsed["cpu"]["aggregate_percent"] == 8.85
    assert len(file_lines) == 1

def test_log_2_file_error(tmp_path):
    log = Logger(str(tmp_path / "test.jsonl"))
    snapshot_dict = log._snapshot_2_dict(make_snapshot())

    # Mock the open file to raise an exception
    with patch("builtins.open") as mock_file:
        mock_file.side_effect = OSError()

        result = log._log_2_file(snapshot_dict)

    assert result is not None
    assert "Couldn't log to file! Error" in result

# -----------------------------------
# Log Snapshot Tests
# -----------------------------------

def test_log_snapshot(tmp_path):
    log = Logger(str(tmp_path / "test.jsonl"))
    result = log.log_snapshot(make_snapshot())

    assert result is None

    file_lines = read_lines(str(tmp_path / "test.jsonl"))
    
    parsed = json.loads(file_lines[0])
    assert parsed["timestamp"] == "2026-03-17 12:00:00"
    assert parsed["cpu"]["aggregate_percent"] == 8.85
    assert len(file_lines) == 1

def test_log_snapshot_double(tmp_path):
    log = Logger(str(tmp_path / "test.jsonl"))
    result = log.log_snapshot(make_snapshot())
    result2 = log.log_snapshot(make_snapshot())

    assert result is None
    assert result2 is None

    file_lines = read_lines(str(tmp_path / "test.jsonl"))

    parsed = json.loads(file_lines[0])
    parsed2 = json.loads(file_lines[1])
    assert parsed["timestamp"] == "2026-03-17 12:00:00"
    assert parsed["cpu"]["aggregate_percent"] == 8.85
    assert parsed2["timestamp"] == "2026-03-17 12:00:00"
    assert parsed2["cpu"]["aggregate_percent"] == 8.85
    assert len(file_lines) == 2

def test_log_snapshot_error(tmp_path):
    log = Logger(str(tmp_path / "test.jsonl"))
    
    # Mock the open file to raise an exception
    with patch("builtins.open") as mock_file:
        mock_file.side_effect = OSError()

        result = log.log_snapshot(make_snapshot())

    assert result is not None
    assert "Couldn't log to file! Error" in result
