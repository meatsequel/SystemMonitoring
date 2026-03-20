from typing import List

from rich.text import Text
from rich.console import Group
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress_bar import ProgressBar

from collector import CpuMetrics, MemoryMetrics, PartitionMetrics, Snapshot, NetworkMetrics
from utils import get_color, format_bytes, format_speed

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
        self.layout['lower'].split_row(
            Layout(name="disk"),
            Layout(name="network")
        )
    
    def _update_cpu_metrics(self, cpu_metric: CpuMetrics) -> Panel:
        """
        Updates the CPU Metrics table

        Args:
            cpu_metric (CpuMetrics): The metrics for the CPU received from the snapshot

        Returns:
            Panel: The panel which has the updated table inside of it
        """
        aggregate_text = Text(f"Total CPU Usage: {cpu_metric.aggregate_percent:.2f}%", justify="center", style=get_color(cpu_metric.aggregate_percent))

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
                                Group(f"[{get_color(core_pct)}]{core_pct}%[/]",
                                      ProgressBar(total=100, completed=core_pct, width=20, complete_style=get_color(core_pct))
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

        mem_table.add_row(format_bytes(memory_metric.total_bytes), 
                          format_bytes(memory_metric.available_bytes), 
                          format_bytes(memory_metric.used_bytes), 
                          format_bytes(memory_metric.free_bytes), 
                          f"[{get_color(memory_metric.percent)}]{memory_metric.percent}%[/]"
                          )

        panel = Panel(
            mem_table,
            title="Memory Usage",
            border_style="bright_black",
            title_align="center",
            padding=(1, 2),
        )

        return panel
    
    def _update_disks_metrics(self, disks_metrics: List[PartitionMetrics], errors: List[str]) -> Panel:
        """
        Updates the Disks Metrics tables

        Args:
            disks_metrics (List[PartitionMetrics]): The list of partition metrics for the disks received from the snapshot
            errors (List[str]): The list of string erros for partition metrics that were omitted

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
                               format_bytes(disk.total_bytes),
                               format_bytes(disk.used_bytes),
                               format_bytes(disk.free_bytes),
                               f"[{get_color(disk.percent)}]{disk.percent}%[/]"
                               )
        
        if errors:
            error_strings = "\n".join(errors)
            errors_text = Text(error_strings, justify="center", style="red")
            render = Group(disk_table, errors_text)
        else:
            render = disk_table

        panel = Panel(
            render,
            title="Disk Usage",
            border_style="bright_black",
            title_align="center",
            padding=(1, 2),
        )

        return panel
    
    def _update_network_metrics(self, interfaces: List[NetworkMetrics]) -> Panel:
        """
        Updates the Network Metrics table

        Args:
            interfaces (List[NetworkMetrics]): The list of network metrics for each interface received from the snapshot

        Returns:
            Panel: The panel which has the updated table inside of it
        """
        network_table = Table(expand=True)
        network_table.add_column("Interface")
        network_table.add_column("Upload Speed")
        network_table.add_column("Download Speed")

        for interface in interfaces:
            if interface.interface:
                network_table.add_row(interface.interface, format_speed(interface.upload), format_speed(interface.download))

        panel = Panel(
            network_table,
            title="Network Usage",
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
        disk_panel = self._update_disks_metrics(snapshot.disks, snapshot.errors)
        network_panel = self._update_network_metrics(snapshot.networks)

        self.layout['upper']['cpu'].update(cpu_panel)
        self.layout['upper']['memory'].update(mem_panel)
        self.layout['lower']['disk'].update(disk_panel)
        self.layout['lower']['network'].update(network_panel)

        return self.layout
