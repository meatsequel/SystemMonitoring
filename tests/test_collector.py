"""
Tests the collector.py functions
All psutil calls are mocked
"""
import datetime as dt

import pytest
import types
from collector import CpuMetrics, MemoryMetrics, PartitionMetrics, DiskResult, Snapshot, NetworkMetrics, get_cpu_utilization, get_virtual_memory, get_disks_statistics, get_snapshot

# -----------------------------------
# CPU Tests
# -----------------------------------

def test_get_cpu_returns_correct_aggregate(monkeypatch):
    def mock_cpu_percent(interval, percpu):
        return [23.2, 1.6, 9.4, 9.4, 15.6, 7.7, 15.6, 6.2, 4.7, 0.0, 12.5, 6.2, 6.2, 6.2, 6.2, 10.9]
        
    monkeypatch.setattr("collector.psutil.cpu_percent", mock_cpu_percent)

    result = get_cpu_utilization(interval=0.0)

    assert isinstance(result, CpuMetrics)
    assert result.per_core_percent == [23.2, 1.6, 9.4, 9.4, 15.6, 7.7, 15.6, 6.2, 4.7, 0.0, 12.5, 6.2, 6.2, 6.2, 6.2, 10.9]
    assert result.aggregate_percent == pytest.approx(8.85)

def test_get_cpu_single_core(monkeypatch):
    def mock_cpu_percent(interval, percpu):
        return [23.2]
        
    monkeypatch.setattr("collector.psutil.cpu_percent", mock_cpu_percent)

    result = get_cpu_utilization(interval=0.0)

    assert isinstance(result, CpuMetrics)
    assert result.per_core_percent == [23.2]
    assert result.aggregate_percent == 23.2

def test_get_cpu_no_core(monkeypatch):
    def mock_cpu_percent(interval, percpu):
        return []
        
    monkeypatch.setattr("collector.psutil.cpu_percent", mock_cpu_percent)

    result = get_cpu_utilization(interval=0.0)
    
    assert isinstance(result, CpuMetrics)
    assert result.per_core_percent == []
    assert result.aggregate_percent == 0.0

# -----------------------------------
# Virtual Memory Tests
# -----------------------------------

def test_get_memory(monkeypatch):
    def mock_virtual_memory():
        return types.SimpleNamespace(total=34257379328, available=19424673792, percent=43.3, used=14832705536, free=19424673792)
    
    monkeypatch.setattr("collector.psutil.virtual_memory", mock_virtual_memory)

    result = get_virtual_memory()
    
    assert isinstance(result, MemoryMetrics)
    assert result.total_bytes == 34257379328
    assert result.available_bytes == 19424673792
    assert result.percent == 43.3
    assert result.used_bytes == 14832705536
    assert result.free_bytes == 19424673792

# -----------------------------------
# Disk Tests
# -----------------------------------

def test_get_disks_returns_correct_partition_data(monkeypatch):
    def mock_disk_partitions():
        return [types.SimpleNamespace(device='C:\\', mountpoint='C:\\', fstype='NTFS', opts='rw,fixed'), ]
    
    def mock_disk_usage(path):
        return types.SimpleNamespace(total=499158196224, used=384801402880, free=114356793344, percent=77.1)
    
    monkeypatch.setattr("collector.psutil.disk_partitions", mock_disk_partitions)
    monkeypatch.setattr("collector.psutil.disk_usage", mock_disk_usage)

    result = get_disks_statistics()

    assert result.errors == []
    assert len(result.partitions) == 1
    assert isinstance(result.partitions[0], PartitionMetrics)
    assert result.partitions[0].device == "C:\\"
    assert result.partitions[0].mountpoint == "C:\\"
    assert result.partitions[0].fstype == "NTFS"
    assert result.partitions[0].total_bytes == 499158196224
    assert result.partitions[0].used_bytes == 384801402880
    assert result.partitions[0].free_bytes == 114356793344
    assert result.partitions[0].percent == 77.1

def test_get_disks_skips_non_mounted_partition(monkeypatch):
    def mock_disk_partitions():
        return [types.SimpleNamespace(device='C:\\', mountpoint='none', fstype='NTFS', opts='rw,fixed'), 
                types.SimpleNamespace(device='E:\\', mountpoint='E:\\', fstype='NTFS', opts='rw,fixed')]
    
    def mock_disk_usage(path):
        if path == "none":
            raise OSError(f"[WinError 3] The system cannot find the path specified: {path}")
        return types.SimpleNamespace(total=499158196224, used=384801402880, free=114356793344, percent=77.1)
    
    monkeypatch.setattr("collector.psutil.disk_partitions", mock_disk_partitions)
    monkeypatch.setattr("collector.psutil.disk_usage", mock_disk_usage)

    result = get_disks_statistics()

    assert len(result.errors) == 1
    assert len(result.partitions) == 1
    assert isinstance(result.partitions[0], PartitionMetrics)
    assert result.partitions[0].mountpoint == "E:\\"

def test_get_disks_all_non_mounted_partition(monkeypatch):
    def mock_disk_partitions():
        return [types.SimpleNamespace(device='C:\\', mountpoint='none', fstype='NTFS', opts='rw,fixed'), 
                types.SimpleNamespace(device='E:\\', mountpoint='none', fstype='NTFS', opts='rw,fixed')]
    
    def mock_disk_usage(path):
        if path == "none":
            raise OSError(f"[WinError 3] The system cannot find the path specified: {path}")
        return types.SimpleNamespace(total=499158196224, used=384801402880, free=114356793344, percent=77.1)
    
    monkeypatch.setattr("collector.psutil.disk_partitions", mock_disk_partitions)
    monkeypatch.setattr("collector.psutil.disk_usage", mock_disk_usage)

    result = get_disks_statistics()

    assert len(result.errors) == 2
    assert len(result.partitions) == 0

def test_get_disks_skips_inaccessible_partition(monkeypatch):
    def mock_disk_partitions():
        return [types.SimpleNamespace(device='C:\\', mountpoint='admin', fstype='NTFS', opts='rw,fixed'), 
                types.SimpleNamespace(device='E:\\', mountpoint='E:\\', fstype='NTFS', opts='rw,fixed')]
    
    def mock_disk_usage(path):
        if path == "admin":
            raise PermissionError(f"[Errno 13] Permission denied: {path}")
        return types.SimpleNamespace(total=499158196224, used=384801402880, free=114356793344, percent=77.1)
    
    monkeypatch.setattr("collector.psutil.disk_partitions", mock_disk_partitions)
    monkeypatch.setattr("collector.psutil.disk_usage", mock_disk_usage)

    result = get_disks_statistics()

    assert len(result.errors) == 1
    assert len(result.partitions) == 1
    assert isinstance(result.partitions[0], PartitionMetrics)
    assert result.partitions[0].mountpoint == "E:\\"

def test_get_disks_all_inaccessible_partition(monkeypatch):
    def mock_disk_partitions():
        return [types.SimpleNamespace(device='C:\\', mountpoint='admin', fstype='NTFS', opts='rw,fixed'), 
                types.SimpleNamespace(device='E:\\', mountpoint='admin', fstype='NTFS', opts='rw,fixed')]
    
    def mock_disk_usage(path):
        if path == "admin":
            raise PermissionError(f"[Errno 13] Permission denied: {path}")
        return types.SimpleNamespace(total=499158196224, used=384801402880, free=114356793344, percent=77.1)
    
    monkeypatch.setattr("collector.psutil.disk_partitions", mock_disk_partitions)
    monkeypatch.setattr("collector.psutil.disk_usage", mock_disk_usage)

    result = get_disks_statistics()

    assert len(result.errors) == 2
    assert len(result.partitions) == 0

def test_get_disks_no_partitions(monkeypatch):
    def mock_disk_partitions():
        return []
    
    monkeypatch.setattr("collector.psutil.disk_partitions", mock_disk_partitions)

    result = get_disks_statistics()

    assert result.errors == []
    assert result.partitions == []

# -----------------------------------
# Snapshot Tests
# -----------------------------------

def make_mock_cpu():
    return CpuMetrics(
        aggregate_percent=8.85,
        per_core_percent=[23.2, 1.6, 9.4, 9.4, 15.6, 7.7, 15.6, 6.2, 4.7, 0.0, 12.5, 6.2, 6.2, 6.2, 6.2, 10.9]
    )

def make_mock_memory():
    return MemoryMetrics(
        total_bytes=34257379328,
        available_bytes=19424673792,
        used_bytes=14832705536,
        free_bytes=19424673792,
        percent=43.3
    )

def make_mock_networks():
    return [
        NetworkMetrics(interface="Ethernet", upload=141826714.54, download=390038572.01),
        NetworkMetrics(interface="Ethernet 2", upload=0, download=0),
    ]

def test_get_snapshot(monkeypatch):
    mock_partitions = [PartitionMetrics(device='C:\\', mountpoint='C:\\', fstype='NTFS', total_bytes=499158196224, used_bytes=384851550208, free_bytes=114306646016, percent=77.1), 
                       PartitionMetrics(device='E:\\', mountpoint='E:\\', fstype='NTFS', total_bytes=1999323250688, used_bytes=1837896716288, free_bytes=161426534400, percent=91.9)] 
    mock_disk_result = DiskResult(
            partitions=mock_partitions,
            errors=[]
        ) 
    mock_cpu_metrics = make_mock_cpu()
    mock_memory_metrics = make_mock_memory()
    mock_network_metrics = make_mock_networks()

    def mock_get_disks_statistics():
        return mock_disk_result

    def mock_get_cpu_utilization(interval):
        return mock_cpu_metrics

    def mock_get_virtual_memory():
        return mock_memory_metrics

    def mock_get_network_statistics(prev_network, interval):
        return mock_network_metrics, {}

    monkeypatch.setattr("collector.get_disks_statistics", mock_get_disks_statistics)
    monkeypatch.setattr("collector.get_cpu_utilization", mock_get_cpu_utilization)
    monkeypatch.setattr("collector.get_virtual_memory", mock_get_virtual_memory)
    monkeypatch.setattr("collector.get_network_statistics", mock_get_network_statistics)

    result, _ = get_snapshot()

    assert isinstance(result, Snapshot)
    assert isinstance(result.timestamp, dt.datetime)
    assert result.disks == mock_partitions
    assert result.errors == []
    assert result.memory == mock_memory_metrics
    assert result.cpu == mock_cpu_metrics
    assert result.networks == mock_network_metrics

def test_get_snapshot_disk_error(monkeypatch):
    mock_partitions = [PartitionMetrics(device='C:\\', mountpoint='C:\\', fstype='NTFS', total_bytes=499158196224, used_bytes=384851550208, free_bytes=114306646016, percent=77.1)] 
    mock_errors = ["[WinError 3] The system cannot find the path specified: none"]
    mock_disk_result = DiskResult(
            partitions=mock_partitions,
            errors=mock_errors
        ) 
    mock_cpu_metrics = make_mock_cpu()
    mock_memory_metrics = make_mock_memory()

    def mock_get_disks_statistics():
        return mock_disk_result

    def mock_get_cpu_utilization(interval):
        return mock_cpu_metrics

    def mock_get_virtual_memory():
        return mock_memory_metrics

    def mock_get_network_statistics(prev_network, interval):
        return [], {}

    monkeypatch.setattr("collector.get_disks_statistics", mock_get_disks_statistics)
    monkeypatch.setattr("collector.get_cpu_utilization", mock_get_cpu_utilization)
    monkeypatch.setattr("collector.get_virtual_memory", mock_get_virtual_memory)
    monkeypatch.setattr("collector.get_network_statistics", mock_get_network_statistics)

    result, _ = get_snapshot()

    assert isinstance(result, Snapshot)
    assert isinstance(result.timestamp, dt.datetime)
    assert result.disks == mock_partitions
    assert result.errors == mock_errors
    assert result.memory == mock_memory_metrics
    assert result.cpu == mock_cpu_metrics
