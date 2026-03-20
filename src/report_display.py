from typing import List

from rich.text import Text
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress_bar import ProgressBar

from report import CpuReport, MemoryReport, DiskReport, ThresholdBreach, Report

# -----------------------------------
# Helper Functions
# -----------------------------------

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
# ReportDisplay Class
# -----------------------------------

class ReportDisplay:
    """
    Responsible for printing the `rich` console display to show daily report.
    Shows the metrics from the report, showing system usage and metrics.
    """
    def __init__(self) -> None:
        """
        Initializes the Display module, and creates the layout for the display
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
            f"[{_get_color(cpu_report.aggregate.min)}]{cpu_report.aggregate.min}%[/]",
            f"[{_get_color(cpu_report.aggregate.max)}]{cpu_report.aggregate.max}%[/]",
            f"[{_get_color(cpu_report.aggregate.avg)}]{cpu_report.aggregate.avg}%[/]",
        )

        for i, core in enumerate(cpu_report.per_core):
            cpu_table.add_row(
                f"Core {i+1}",
                f"[{_get_color(core.min)}]{core.min}%[/]",
                f"[{_get_color(core.max)}]{core.max}%[/]",
                f"[{_get_color(core.avg)}]{core.avg}%[/]",
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
            f"[{_get_color(memory_report.percent.min)}]{memory_report.percent.min}%[/]",
            f"[{_get_color(memory_report.percent.max)}]{memory_report.percent.max}%[/]",
            f"[{_get_color(memory_report.percent.avg)}]{memory_report.percent.avg}%[/]",
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
                f"[{_get_color(disk.percent.min)}]{disk.percent.min}%[/]",
                f"[{_get_color(disk.percent.max)}]{disk.percent.max}%[/]",
                f"[{_get_color(disk.percent.avg)}]{disk.percent.avg}%[/]",
            )

        panel = Panel(
            disks_table,
            title="Disk Usage",
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

        if report.breaches:
            self.console.print(self._render_breaches(report.breaches))
