from rich.live import Live
import argparse

import collector
from display import Display
from logger import Logger
from report import get_report
from report_display import ReportDisplay

# -----------------------------------
# Monitor
# -----------------------------------

def run_monitor(interval: float, path: str) -> None:
    """
    Main function called to run the collector, logger and display

    Args:
        interval (float): Interval to monitor system at
        path (str): Path to log system readings to
    """
    log = Logger(path=path)
    disp = Display()
    prev_network = None

    with Live(disp.layout, refresh_per_second=4, screen=True) as live:
        while True:
            snapshot, prev_network = collector.get_snapshot(interval=interval, prev_network=prev_network)
            live.update(disp.update_display(snapshot=snapshot))
            log.log_snapshot(snapshot=snapshot)

# -----------------------------------
# Report
# -----------------------------------

def run_report(path: str, date: str, cpu_warn: float | None, mem_warn: float | None, disk_warn: float | None,
               net_up_warn: float | None, net_dwn_warn: float | None):
    """
    Main function called to generate daily report and to present it

    Args:
        path (str): Path to log file to read from
        date (str): Date to report on, in YYYY-MM-DD format
        cpu_warn (float | None): CPU  threshold percentage to check for breaches
        mem_warn (float | None): Memory threshold percentage to check for breaches
        disk_warn (float | None): Disk threshold percentage to check for breaches
        net_up_warn (float | None): Upload speed threshold in Mbps to check for breaches
        net_dwn_warn (float | None): Download speed threshold in Mbps to check for breaches
    """
    result = get_report(
        path=path,
        date=date,
        cpu_threshold=cpu_warn,
        mem_threshold=mem_warn,
        disk_threshold=disk_warn,
        net_up_threshold=net_up_warn,
        net_dwn_threshold=net_dwn_warn,
    )

    if isinstance(result, str):
        print(result)
        return

    ReportDisplay().render_report(result)

# -----------------------------------
# Entry Point
# -----------------------------------

def main():
    parser = argparse.ArgumentParser(prog="sysmon")
    subparsers = parser.add_subparsers(dest="command")

    monitor_parser = subparsers.add_parser("monitor", help="Run the live system monitor")
    monitor_parser.add_argument("--interval", help="Interval to monitor system at", type=float, default=2.0)
    monitor_parser.add_argument("--log", help="Path to log system readings to", type=str, default="log.jsonl")

    report_parser = subparsers.add_parser("report", help="Generate a daily report from a log file")
    report_parser.add_argument("--date", help="Date to report on in YYYY-MM-DD format", type=str, required=True)
    report_parser.add_argument("--log", help="Path to the log file to read from", type=str, default="log.jsonl")
    report_parser.add_argument("--cpu-warn", help="CPU threshold percentage to check for breaches", type=float, default=None)
    report_parser.add_argument("--mem-warn", help="Memory threshold percentage to check for breaches", type=float, default=None)
    report_parser.add_argument("--disk-warn", help="Disk threshold percentage to check for breaches", type=float, default=None)
    report_parser.add_argument("--net-up-warn", help="Upload speed threshold in Mbps to check for breaches", type=float, default=None)
    report_parser.add_argument("--net-dwn-warn", help="Download speed threshold in Mbps to check for breaches", type=float, default=None)

    args = parser.parse_args()

    if args.command == "monitor":
        if args.interval < 0.1:
            monitor_parser.error("--interval must be at least 0.1")
        try:
            run_monitor(args.interval, args.log)
        except KeyboardInterrupt:
            print("Shutting down...")
    elif args.command == "report":
        run_report(
            path=args.log,
            date=args.date,
            cpu_warn=args.cpu_warn,
            mem_warn=args.mem_warn,
            disk_warn=args.disk_warn,
            net_up_warn=args.net_up_warn,
            net_dwn_warn=args.net_dwn_warn,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
