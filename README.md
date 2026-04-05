# SysMon

A command-line tool that tracks CPU, memory, disk, and network usage in real time. It shows a live terminal dashboard, logs every reading to a JSON file, and has a report command to look at daily stats from those logs.

---

## Installation

Python 3.10+ is required. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install psutil rich
```

To install it as a CLI tool so you can type `sysmon` instead of `python main.py`:

```bash
pip install -e .
```

---

## Usage

### Live Monitor

```bash
python main.py monitor
sysmon monitor
```

Polls every 2 seconds by default and logs to `log.jsonl` in the current directory. Stop with `Ctrl+C`.

```bash
python main.py monitor --interval 5 --log /path/to/mylog.jsonl
sysmon monitor --interval 5 --log /path/to/mylog.jsonl
```

Minimum interval is `0.1` seconds — passing `0` caused psutil to return cached values and flooded the log instantly.

### Daily Report

```bash
python main.py report --date 2026-03-19
sysmon report --date 2026-03-19

python main.py report --date 2026-03-19 --log /path/to/mylog.jsonl
sysmon report --date 2026-03-19 --log /path/to/mylog.jsonl
```

Prints min, avg, and max for CPU, memory, disks, and network for that date.

To check for threshold breaches — network thresholds are in Mbps:

```bash
python main.py report --date 2026-03-19 --cpu-warn 80 --mem-warn 85 --disk-warn 90 --net-up-warn 500 --net-dwn-warn 500
sysmon report --date 2026-03-19 --cpu-warn 80 --mem-warn 85 --disk-warn 90 --net-up-warn 500 --net-dwn-warn 500
```

Any metric that hit or exceeded its threshold shows up in a red panel at the bottom. You don't need to pass all of them, the report still works without any.

---

## Flags

### `monitor`

| Flag | Default | Description |
|---|---|---|
| `--interval` | `2.0` | Polling interval in seconds (min 0.1) |
| `--log` | `log.jsonl` | Path to log file |

### `report`

| Flag | Default | Description |
|---|---|---|
| `--date` | *(required)* | Date in `YYYY-MM-DD` format |
| `--log` | `log.jsonl` | Path to log file |
| `--cpu-warn` | None | CPU threshold % |
| `--mem-warn` | None | Memory threshold % |
| `--disk-warn` | None | Disk threshold % |
| `--net-up-warn` | None | Upload threshold in Mbps |
| `--net-dwn-warn` | None | Download threshold in Mbps |

---

## Project Structure

```
sysmon/
├── src/
│   ├── collector.py      # CPU, memory, disk, and network metrics
│   ├── display.py        # Live terminal dashboard
│   ├── logger.py         # Writes snapshots to the log file as JSON
│   ├── report.py         # Reads the log and computes daily stats
│   ├── report_display.py # Prints the report to the terminal
│   ├── utils.py          # Byte formatting, color coding, shared helpers
│   └── main.py           # Entry point, CLI argument parsing
├── tests/
│   ├── test_collector.py
│   ├── test_logger.py
│   └── test_report.py
└── docs/
    └── design.md
```

---

## Running Tests

```bash
pytest
```

All psutil calls and file I/O are mocked so tests never touch real system state.
