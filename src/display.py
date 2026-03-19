from typing import List

from rich.text import Text
from rich.console import Group
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress_bar import ProgressBar

from collector import CpuMetrics, MemoryMetrics, PartitionMetrics, Snapshot

# -----------------------------------
# Helper Functions
# -----------------------------------

def _bytes_to_gb(num_bytes: int) -> float:
    """
    Method which takes bytes and converts it  to GB

    Args:
        num_bytes (int): The amount of bytes

    Returns:
        float: The bytes converted to GB
    """
    return num_bytes / 1024 / 1024 / 1024

def _bytes_to_mb(num_bytes: int) -> float:
    """
    Method which takes bytes and converts it to MB

    Args:
        num_bytes (int): The amount of bytes

    Returns:
        float: The bytes converted to MB
    """
    return num_bytes / 1024 / 1024

def _format_bytes(num_bytes: int) -> str:
    """
    Method which takes bytes and decides if to convert it to MB or GB

    Args:
        num_bytes (int): The amount of bytes

    Returns:
        str: The bytes converted to either MB or GB as a string
    """
    if num_bytes > 1024 * 1024 * 1024:
        return f"{_bytes_to_gb(num_bytes):.2f} GB"
    return f"{_bytes_to_mb(num_bytes):.2f} MB"

def _get_color(percent: float) -> str:
    """
    Takes a percentage input and converts it to a rich color name

    Args:
        percent (float): Percent used / full

    Returns:
        str: A rich color name based on the percentage
    """
    if percent >= 90.0:
        return "red"
    if percent >= 75.0:
        return "orange1"
    if percent >= 60.0:
        return "yellow"
    return "green"

# -----------------------------------
# Display Class
# -----------------------------------

class Display:
    """
    Responsible for creating the `rich` console display. Has live updates.
    Shows the metrics from the snapshot, showing system usage and metrics.
    """
    def __init__(self) -> None:
        """
        Initializes the Display module, and creates the layout for the display
        """
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="upper"),
            Layout(name="lower")
        )
        self.layout['upper'].split_row(
            Layout(name="cpu"),
            Layout(name="memory")
        )
    
    def _update_cpu_metrics(self, cpu_metric: CpuMetrics) -> Panel:
        """
        Updates the CPU Metrics table

        Args:
            cpu_metric (CpuMetrics): The metrics for the CPU received from the snapshot

        Returns:
            Panel: The panel which has the updated table inside of it
        """
        aggregate_text = Text(f"Total CPU Usage: {cpu_metric.aggregate_percent:.2f}%", justify="center", style=_get_color(cpu_metric.aggregate_percent))

        cores = cpu_metric.per_core_percent
        cores_per_row = 2
        
        cpu_table = Table(expand=True)

        # Add core and usage columns per group
        for _ in range(cores_per_row):
            cpu_table.add_column("Core")
            cpu_table.add_column("Usage %")

        remainder = len(cores) % cores_per_row
        padded = list(cores)
        if remainder:
            padded += [None] * (cores_per_row - remainder)

        num_rows = len(padded) // cores_per_row

        for row_idx in range(num_rows):
            row = []
            for col in range(cores_per_row):
                # Table gets filled top to bottom, left to right
                core_pct = padded[row_idx + col * num_rows]
                if core_pct is None:
                    row.extend(["", ""])
                else:
                    row.extend([str(row_idx + col * num_rows + 1),
                                Group(f"[{_get_color(core_pct)}]{core_pct}%[/]",
                                      ProgressBar(total=100, completed=core_pct, width=20, complete_style=_get_color(core_pct))
                                      )
                                ])

            cpu_table.add_row(*row)

        panel = Panel(
            Group(aggregate_text, cpu_table),
            title="CPU Usage",
            border_style="bright_black",
            title_align="center",
            padding=(1, 2),
        )

        return panel
    
    def _update_memory_metrics(self, memory_metric: MemoryMetrics) -> Panel:
        """
        Updates the Memory Metrics table

        Args:
            memory_metric (MemoryMetrics): The metrics for the memory received from the snapshot

        Returns:
            Panel: The panel which has the updated table inside of it
        """
        mem_table = Table(expand=True)
        mem_table.add_column("Total")
        mem_table.add_column("Available")
        mem_table.add_column("Used")
        mem_table.add_column("Free")
        mem_table.add_column("Usage %")

        mem_table.add_row(_format_bytes(memory_metric.total_bytes), 
                          _format_bytes(memory_metric.available_bytes), 
                          _format_bytes(memory_metric.used_bytes), 
                          _format_bytes(memory_metric.free_bytes), 
                          f"[{_get_color(memory_metric.percent)}]{memory_metric.percent}%[/]"
                          )

        panel = Panel(
            mem_table,
            title="Memory Usage",
            border_style="bright_black",
            title_align="center",
            padding=(1, 2),
        )

        return panel
    
    def _update_disks_metrics(self, disks_metrics: List[PartitionMetrics]) -> Panel:
        """
        Updates the Disks Metrics tables

        Args:
            disks_metrics (List[PartitionMetrics]): The list of partition metrics for the disks received from the snapshot

        Returns:
            Panel: The panel which has the updated tables inside of it
        """
        disk_table = Table(expand=True)
        disk_table.add_column("Device")
        disk_table.add_column("Mount Point")
        disk_table.add_column("File System Type")
        disk_table.add_column("Total")
        disk_table.add_column("Used")
        disk_table.add_column("Free")
        disk_table.add_column("Usage %")

        for disk in disks_metrics:
            disk_table.add_row(disk.device, disk.mountpoint, disk.fstype,
                               _format_bytes(disk.total_bytes),
                               _format_bytes(disk.used_bytes),
                               _format_bytes(disk.free_bytes),
                               f"[{_get_color(disk.percent)}]{disk.percent}%[/]"
                               )

        panel = Panel(
            disk_table,
            title="Disk Usage",
            border_style="bright_black",
            title_align="center",
            padding=(1, 2),
        )

        return panel

    def update_display(self, snapshot: Snapshot) -> Layout:
        """
        Updates the entire display with the new metrics given from the snapshot

        Args:
            snapshot (Snapshot): The snapshot from collector with the new metrics

        Returns:
            Layout: The updated layout with the new metrics
        """
        cpu_panel = self._update_cpu_metrics(snapshot.cpu)
        mem_panel = self._update_memory_metrics(snapshot.memory)
        disk_panel = self._update_disks_metrics(snapshot.disks)
        
        self.layout['upper']['cpu'].update(cpu_panel)
        self.layout['upper']['memory'].update(mem_panel)
        self.layout['lower'].update(disk_panel)

        return self.layout
