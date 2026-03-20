import datetime as dt
from typing import List, Tuple
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
class NetworkMetrics:
    """Network speed for a single interface at a point in time"""
    interface: str
    upload: float
    download: float

@dataclass
class Snapshot:
    """Complete system metric"""
    timestamp: dt.datetime
    cpu: CpuMetrics
    memory: MemoryMetrics
    disks: List[PartitionMetrics]
    errors: List[str]
    networks: List[NetworkMetrics]


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

def get_network_statistics(prev_network: dict | None, interval: float) -> Tuple[List[NetworkMetrics], dict]:
    """
    Gets the network upload and download speed for each interface.
    On the first call with no previous reading, returns empty speeds.

    Args:
        prev_network (dict | None): Raw network counters from the previous call, or None on first call
        interval (float): Sampling window in seconds, used to calculate bytes per second

    Returns:
        Tuple of a list of NetworkMetrics for each interface and the current raw counters for the next call
    """
    curr_network = psutil.net_io_counters(pernic=True)

    if not prev_network:
        return [], curr_network

    interfaces = []
    for interface, stats in curr_network.items():
        previous_stats = prev_network.get(interface, None)
        if previous_stats:
            dwn_spd = max(0, (stats.bytes_recv - previous_stats.bytes_recv) / interval)
            up_speed = max(0, (stats.bytes_sent - previous_stats.bytes_sent) / interval)
            interfaces.append(
                NetworkMetrics(
                    interface=interface,
                    upload=up_speed,
                    download=dwn_spd
                )
            )

    return interfaces, curr_network

# -----------------------------------
# Snapshot
# -----------------------------------

def get_snapshot(interval: float = 1.0, prev_network: dict | None = None) -> Tuple[Snapshot, dict]:
    """
    Gets a snapshot of the current overall system statistics and usages.

    Args:
        interval (float): Sampling window in seconds used for get_cpu_utilization(), and to calculate the network speeds
        prev_network (dict | None): Raw network counters from the previous snapshot, or None on first call

    Returns:
        Tuple of the Snapshot with all metrics filled and the current raw network counters for the next call.
        Any partitions that had an error while trying to be read will be ommitted from disk.
        The reason for their error can be seen in Snapshot.errors
    """
    disk_result = get_disks_statistics()
    network_speeds, curr_network = get_network_statistics(prev_network, interval)
    return Snapshot(
        timestamp=dt.datetime.now(dt.timezone.utc),
        cpu=get_cpu_utilization(interval),
        memory=get_virtual_memory(),
        disks=disk_result.partitions,
        errors=disk_result.errors,
        networks=network_speeds,
    ), curr_network
