from typing import List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from report import CpuReport, MemoryReport, DiskReport, ThresholdBreach, Report, NetworkInterfaceReport
from utils import get_color, format_speed

# -----------------------------------
# ReportDisplay Class
# -----------------------------------

class ReportDisplay:
    """
    Responsible for printing the `rich` console display to show daily report.
    Shows the metrics from the report, showing system usage and metrics.
    """
    def __init__(self) -> None:
        """
        Initializes the ReportDisplay with a rich Console
        """
        self.console = Console()

    def _render_cpu(self, cpu_report: CpuReport) -> Panel:
        """
        Renders the CPU stats table

        Args:
            cpu_report (CpuReport): The computed CPU metrics from the report

        Returns:
            Panel: The panel which has the table inside of it
        """
        cpu_table = Table(expand=True)
        cpu_table.add_column("Metric")
        cpu_table.add_column("Min %")
        cpu_table.add_column("Max %")
        cpu_table.add_column("Avg %")

        cpu_table.add_row(
            "Aggregate",
            f"[{get_color(cpu_report.aggregate.min)}]{cpu_report.aggregate.min}%[/]",
            f"[{get_color(cpu_report.aggregate.max)}]{cpu_report.aggregate.max}%[/]",
            f"[{get_color(cpu_report.aggregate.avg)}]{cpu_report.aggregate.avg}%[/]",
        )

        for i, core in enumerate(cpu_report.per_core):
            cpu_table.add_row(
                f"Core {i+1}",
                f"[{get_color(core.min)}]{core.min}%[/]",
                f"[{get_color(core.max)}]{core.max}%[/]",
                f"[{get_color(core.avg)}]{core.avg}%[/]",
            )

        panel = Panel(
            cpu_table,
            title="CPU Usage",
            border_style="bright_black",
            title_align="center",
            padding=(1, 2),
        )

        return panel

    def _render_memory(self, memory_report: MemoryReport) -> Panel:
        """
        Renders the memory stats table

        Args:
            memory_report (MemoryReport): The computed memory metrics from the report

        Returns:
            Panel: The panel which has the table inside of it
        """
        memory_table = Table(expand=True)
        memory_table.add_column("Metric")
        memory_table.add_column("Min %")
        memory_table.add_column("Max %")
        memory_table.add_column("Avg %")

        memory_table.add_row(
            "Memory",
            f"[{get_color(memory_report.percent.min)}]{memory_report.percent.min}%[/]",
            f"[{get_color(memory_report.percent.max)}]{memory_report.percent.max}%[/]",
            f"[{get_color(memory_report.percent.avg)}]{memory_report.percent.avg}%[/]",
        )

        panel = Panel(
            memory_table,
            title="Memory Usage",
            border_style="bright_black",
            title_align="center",
            padding=(1, 2),
        )

        return panel

    def _render_disks(self, disks: List[DiskReport]) -> Panel:
        """
        Renders the disks stats table

        Args:
            disks (List[DiskReport]): The computed disks metrics from the report

        Returns:
            Panel: The panel which has the table inside of it
        """
        disks_table = Table(expand=True)
        disks_table.add_column("Device")
        disks_table.add_column("Mount Point")
        disks_table.add_column("Min %")
        disks_table.add_column("Max %")
        disks_table.add_column("Avg %")

        for disk in disks:
            disks_table.add_row(
                disk.device,
                disk.mountpoint,
                f"[{get_color(disk.percent.min)}]{disk.percent.min}%[/]",
                f"[{get_color(disk.percent.max)}]{disk.percent.max}%[/]",
                f"[{get_color(disk.percent.avg)}]{disk.percent.avg}%[/]",
            )

        panel = Panel(
            disks_table,
            title="Disk Usage",
            border_style="bright_black",
            title_align="center",
            padding=(1, 2),
        )

        return panel

    def _render_networks(self, interfaces: List[NetworkInterfaceReport]) -> Panel:
        """
        Renders the network stats table

        Args:
            interfaces (List[NetworkInterfaceReport]): The computed network metrics from the report

        Returns:
            Panel: The panel which has the table inside of it
        """
        networks_table = Table(expand=True)
        networks_table.add_column("Interface")
        networks_table.add_column("Min Upload")
        networks_table.add_column("Max Upload")
        networks_table.add_column("Avg Upload")
        networks_table.add_column("Min Download")
        networks_table.add_column("Max Download")
        networks_table.add_column("Avg Download")

        for interface in interfaces:
            networks_table.add_row(
                interface.interface,
                format_speed(interface.upload.min),
                format_speed(interface.upload.max),
                format_speed(interface.upload.avg),
                format_speed(interface.download.min),
                format_speed(interface.download.max),
                format_speed(interface.download.avg),
            )

        panel = Panel(
            networks_table,
            title="Network Usage",
            border_style="bright_black",
            title_align="center",
            padding=(1, 2),
        )

        return panel

    def _render_breaches(self, breaches: List[ThresholdBreach]) -> Panel:
        """
        Renders the threshold breaches table

        Args:
            breaches (List[ThresholdBreach]): The list of threshold breaches

        Returns:
            Panel: The panel which has the table inside of it
        """
        breaches_table = Table(expand=True)
        breaches_table.add_column("Metric")
        breaches_table.add_column("Threshold %")
        breaches_table.add_column("Max %")

        for breach in breaches:
            breaches_table.add_row(
                breach.metric,
                f"{breach.threshold}",
                f"[red]{breach.max_percent}%[/]",
            )

        panel = Panel(
            breaches_table,
            title="Threshold Breaches",
            border_style="red",
            title_align="center",
            padding=(1, 2),
        )

        return panel

    def render_report(self, report: Report) -> None:
        """
        Renders the full report

        Args:
            report (Report): The computed report
        """
        self.console.print(f"Daily Report - {report.date} - {report.num_snapshots} snapshots")
        self.console.print(self._render_cpu(report.cpu))
        self.console.print(self._render_memory(report.memory))
        self.console.print(self._render_disks(report.disks))
        self.console.print(self._render_networks(report.networks))

        if report.breaches:
            self.console.print(self._render_breaches(report.breaches))
