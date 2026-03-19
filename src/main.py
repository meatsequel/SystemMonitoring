from rich.live import Live
import argparse

import collector
from display import Display
from logger import Logger

def run_monitor(interval: float, path: str) -> None:
    """
    Main function called to run the collector, logger and display

    Args:
        interval (float): Interval to monitor system at
        path (str): Path to log system readings to
    """
    log = Logger(path=path)
    disp = Display()

    with Live(disp.layout, refresh_per_second=4, screen=True) as live:
        while True:
            snapshot = collector.get_snapshot(cpu_interval=interval)
            live.update(disp.update_display(snapshot=snapshot))
            log.log_snapshot(snapshot=snapshot)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", help="Interval to monitor system at", type=float, default=2.0)
    parser.add_argument("--log", help="Path to log system readings to", type=str, default="log.jsonl")
    
    args = parser.parse_args()
    if args.interval < 0.1:
        parser.error("--interval must be at least 0.1")

    try:
        run_monitor(args.interval, args.log)
    except KeyboardInterrupt:
        print("Shutting down...")
