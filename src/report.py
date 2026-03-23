import json
from typing import List
from dataclasses import dataclass

from utils import bytes_to_mb

# -----------------------------------
# Data Types
# -----------------------------------

@dataclass
class MetricStats:
    """Min, avg and max statistics for a single metric"""
    min: float
    avg: float
    max: float

@dataclass
class CpuReport:
    """CPU statistics for the report"""
    aggregate: MetricStats
    per_core: List[MetricStats]

@dataclass
class MemoryReport:
    """Memory statistics for the report"""
    percent: MetricStats

@dataclass
class DiskReport:
    """Disk statistics for a single partition"""
    device: str
    mountpoint: str
    percent: MetricStats

@dataclass
class NetworkInterfaceReport:
    """Network statistics for a single interface"""
    interface: str
    upload: MetricStats
    download: MetricStats

@dataclass
class ThresholdBreach:
    """A single threshold breach entry"""
    metric: str
    threshold: float
    max_value: float
    unit: str

@dataclass
class Report:
    """Complete daily report for a given date"""
    date: str
    num_snapshots: int
    cpu: CpuReport
    memory: MemoryReport
    disks: List[DiskReport]
    networks: List[NetworkInterfaceReport]
    breaches: List[ThresholdBreach]

# -----------------------------------
# Helpers
# -----------------------------------

def _read_log(path: str, date: str) -> List[dict] | str:
    """
    Reads the log and filters for snapshots from the given date

    Args:
        path (str): The path to the log file
        date (str): Date to filter snapshots from

    Return
        List[dict]: Each snapshot entry as a dict from the given date
        or a string error message if the file couldn't be read
    """
    file_lines = []
    try:
        with open(path, "r") as fl:
            for line in fl:
                file_lines.append(line)
    except OSError as e:
        return f"Could not read log file at {path}! Error {e}"
    
    log_entries = []
    for line in file_lines:
        try:
            entry = json.loads(line.strip())
            if entry["timestamp"].startswith(date):
                log_entries.append(entry)
        except json.JSONDecodeError:
            continue

    return log_entries

def _compute_stats(values: List[float]) -> MetricStats:
    """
    Computes min, max and avg for the values

    Args:
        values (List[float]): The list of values to compute stats for

    Returns:
        MetricStats with min, avg and max
    """
    if not values:
        return MetricStats(
            min=0.0,
            avg=0.0,
            max=0.0
        )
    return MetricStats(
        min=round(min(values), 2),
        avg=round(sum(values) / len(values), 2),
        max=round(max(values), 2)
    )

def _check_breaches(cpu_report: CpuReport, memory_report: MemoryReport, disks_reports: List[DiskReport], networks_reports: List[NetworkInterfaceReport],
                    cpu_threshold: float | None, mem_threshold: float | None, disk_threshold: float | None,
                    net_up_threshold: float | None, net_dwn_threshold: float | None
                    ) -> List[ThresholdBreach]:
    """
    Checks the stats and looks at the thresholds, returns any breaches that went over the threshold

    Args:
        cpu_report (CpuReport): The computed CPU report
        memory_report (MemoryReport): The computed memory report
        disks_reports (List[DiskReport]): The computed disk reports
        networks_reports (List[NetworkInterfaceReport]): The computed network reports
        cpu_threshold (float | None): CPU threshold percentage or None to skip
        mem_threshold (float | None): Memory threshold percentage or None to skip
        disk_threshold (float | None): Disk threshold percentage or None to skip
        net_up_threshold (float | None): Upload speed threshold in Mbps or None to skip
        net_dwn_threshold (float | None): Download speed threshold in Mbps or None to skip

    Returns:
        List[ThresholdBreach] of any breaches found
    """
    breaches = []

    if cpu_threshold:
        if cpu_report.aggregate.max >= cpu_threshold:
            breaches.append(ThresholdBreach(
                metric="CPU Aggregate",
                threshold=cpu_threshold,
                max_value=cpu_report.aggregate.max,
                unit="%"
            ))
        for i, core in enumerate(cpu_report.per_core):
            if core.max >= cpu_threshold:
                breaches.append(ThresholdBreach(
                    metric=f"CPU Core {i+1}",
                    threshold=cpu_threshold,
                    max_value=core.max,
                    unit="%"
                ))

    if mem_threshold:
        if memory_report.percent.max >= mem_threshold:
            breaches.append(ThresholdBreach(
                metric="Memory",
                threshold=mem_threshold,
                max_value=memory_report.percent.max,
                unit="%"
            ))

    if disk_threshold:
        for disk_report in disks_reports:
            if disk_report.percent.max >= disk_threshold:
                breaches.append(ThresholdBreach(
                    metric=f"Disk {disk_report.mountpoint}",
                    threshold=disk_threshold,
                    max_value=disk_report.percent.max,
                    unit="%"
                ))

    if net_up_threshold:
        for net_report in networks_reports:
            max_upload_mbps = round(bytes_to_mb(net_report.upload.max) * 8, 2)
            if max_upload_mbps >= net_up_threshold:
                breaches.append(ThresholdBreach(
                    metric=f"Upload {net_report.interface}",
                    threshold=net_up_threshold,
                    max_value=max_upload_mbps,
                    unit="Mbps"
                ))

    if net_dwn_threshold:
        for net_report in networks_reports:
            max_download_mbps = round(bytes_to_mb(net_report.download.max) * 8, 2)
            if max_download_mbps >= net_dwn_threshold:
                breaches.append(ThresholdBreach(
                    metric=f"Download {net_report.interface}",
                    threshold=net_dwn_threshold,
                    max_value=max_download_mbps,
                    unit="Mbps"
                ))

    return breaches

# -----------------------------------
# Report
# -----------------------------------

def get_report(path: str, date: str, cpu_threshold: float | None = None, mem_threshold: float | None = None, disk_threshold: float | None = None,
               net_up_threshold: float | None = None, net_dwn_threshold: float | None = None) -> Report | str:
    """
    Reads the log file and computes a daily report for the given date

    Args:
        path (str): Path to the log file
        date (str): Date to report on in YYYY-MM-DD format
        cpu_threshold (float | None): CPU threshold percentage to check for breaches
        mem_threshold (float | None): Memory threshold percentage to check for breaches
        disk_threshold (float | None): Disk threshold percentage to check for breaches
        net_up_threshold (float | None): Upload speed threshold in Mbps to check for breaches
        net_dwn_threshold (float | None): Download speed threshold in Mbps to check for breaches

    Returns:
        Report with all stats and breaches filled, or an error string if the log
        could not be read or no entries were found for the given date
    """
    log_entries = _read_log(path, date)

    if not log_entries:
        return f"No entries found in {path} for {date}"

    if isinstance(log_entries, str):
        return log_entries

    ## CPU Stats
    cpu_agg = [entry["cpu"]["aggregate_percent"] for entry in log_entries]
    cpu_aggregate_stats = _compute_stats(cpu_agg)

    num_cores = len(log_entries[0]["cpu"]["per_core_percent"])
    per_core_stats = []
    for i in range(num_cores):
        cpu_per_core = [entry["cpu"]["per_core_percent"][i] for entry in log_entries]
        per_core_stats.append(_compute_stats(cpu_per_core))

    cpu_report = CpuReport(aggregate=cpu_aggregate_stats, per_core=per_core_stats)

    ## Memory Stats
    mem_pct = [entry["memory"]["percent"] for entry in log_entries]
    memory_report = MemoryReport(_compute_stats(mem_pct))

    ## Disk Stats

    # group disks by mountpoint
    disk_map = {}
    for entry in log_entries:
        for disk in entry["disks"]:
            mountpoint = disk["mountpoint"]
            if mountpoint not in disk_map:
                disk_map[mountpoint] = {"device": disk["device"], "values": []}
            disk_map[mountpoint]["values"].append(disk["percent"])

    disks_reports = []
    for mountpoint, data in disk_map.items():
        disks_reports.append(DiskReport(
            device=data["device"],
            mountpoint=mountpoint,
            percent=_compute_stats(data["values"]),
        ))

    ## Network Stats

    # group speeds by interface
    network_map = {}
    for entry in log_entries:
        if "networks" not in entry:
            continue
        for speed in entry["networks"]:
            interface = speed["interface"]
            if interface not in network_map:
                network_map[interface] = {"upload": [], "download": []}
            network_map[interface]["upload"].append(speed["upload"])
            network_map[interface]["download"].append(speed["download"])

    networks_reports = []
    for interface, data in network_map.items():
        networks_reports.append(NetworkInterfaceReport(
            interface=interface,
            upload=_compute_stats(data["upload"]),
            download=_compute_stats(data["download"]),
        ))

    breaches = _check_breaches(
        cpu_report=cpu_report,
        memory_report=memory_report,
        disks_reports=disks_reports,
        networks_reports=networks_reports,
        cpu_threshold=cpu_threshold,
        mem_threshold=mem_threshold,
        disk_threshold=disk_threshold,
        net_up_threshold=net_up_threshold,
        net_dwn_threshold=net_dwn_threshold,
    )

    return Report(
        date=date,
        num_snapshots=len(log_entries),
        cpu=cpu_report,
        memory=memory_report,
        disks=disks_reports,
        networks=networks_reports,
        breaches=breaches,
    )
