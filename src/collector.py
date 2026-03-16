import datetime as dt
from typing import List
from dataclasses import dataclass

import psutil

# -----------------------------------
# Data Types
# -----------------------------------

@dataclass
class CpuMetrics:
    """CPU utilization at time"""
    aggregate_percent: float
    per_core_percent: List[float]

@dataclass
class MemoryMetrics:
    """Virtual memory statistics"""
    total_bytes: int
    available_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float

@dataclass
class PartitionMetrics:
    """Disk usage for a single partition"""
    device: str
    mountpoint: str
    fstype: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float

@dataclass
class DiskResult:
    """Return type for get_disks_statistics, bundling partition and errors together"""
    partitions: List[PartitionMetrics]
    errors: List[str]

@dataclass
class Snapshot:
    """Complete system metric"""
    timestamp: dt.datetime
    cpu: CpuMetrics
    memory: MemoryMetrics
    disks: List[PartitionMetrics]
    errors: List[str]


# -----------------------------------
# Collectors
# -----------------------------------

def get_cpu_utilization(interval: float = 1.0) -> CpuMetrics:
    """
    Get CPU utilization percentage for the sampling window.

    Args:
        interval (float): Sampling window in seconds

    Returns:
        CpuMetrics with aggreate and per core utilzation percentages
    """
    per_core = psutil.cpu_percent(interval=interval, percpu=True)
    aggregate = sum(per_core) / len(per_core) if per_core else 0.0
    return CpuMetrics(
        aggregate_percent=aggregate, per_core_percent=per_core
        )

def get_virtual_memory() -> MemoryMetrics:
    """
    Gets the system virtual memory usage in bytes

    Returns:
        MemoryMetrics with total, available, used, free bytes and percentage used
    """
    virtual_mem = psutil.virtual_memory()
    return MemoryMetrics(
        total_bytes=virtual_mem.total,
        available_bytes=virtual_mem.available,
        used_bytes=virtual_mem.used,
        free_bytes=virtual_mem.free,
        percent=virtual_mem.percent
    )

def get_disks_statistics() -> DiskResult:
    """
    Returns usage statistics for every currently mounted partition.

    Returns:
        DiskResult with a list of PartitionMetrics for each accessible partition
        and a list of error strings for any partitions that could not be read.
    """
    partitions = []
    errors = []

    for part in psutil.disk_partitions():
        try:
            part_usage = psutil.disk_usage(part.mountpoint)
            partitions.append(PartitionMetrics(
                device=part.device,
                mountpoint=part.mountpoint,
                fstype=part.fstype,
                total_bytes=part_usage.total,
                used_bytes=part_usage.used,
                free_bytes=part_usage.free,
                percent=part_usage.percent,
            ))
        except (PermissionError, OSError) as e:
            errors.append(f"Could not read partition {part.mountpoint}! Error {e}")
    
    return DiskResult(partitions=partitions, errors=errors)

# -----------------------------------
# Snapshot
# -----------------------------------

def get_snapshot(cpu_interval: float = 1.0) -> Snapshot:
    """
    Gets a snapshot of the current overall system statistics and usages.

    Args:
        cpu_interval (float): Sampling window in seconds used for get_cpu().

    Returns:
        Snapshot with timestamp (UTC), cpu, memory, disk and errors all filled accordingly.
        Any partitions that had an error while trying to be read will be ommitted from disk.
        The reason for their error can be seen in Snapshot.errors
    """
    disk_result = get_disks_statistics()
    return Snapshot(
        timestamp=dt.datetime.now(dt.timezone.utc),
        cpu=get_cpu_utilization(cpu_interval),
        memory=get_virtual_memory(),
        disks=disk_result.partitions,
        errors=disk_result.errors,
    )