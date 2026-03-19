# SysMon – Design Document

## Design Decisions

Start off by reading psutil documentation to understand what functions I needed and what they return. Sketch on the side what functions I want to write, and what data types they should return before writing any code.

1. Start off with writing the `collector.py` file
    - Decided to use module-level functions instead of a class. Since `interval` only affected `get_cpu_utilization`, there was no shared state to justify using a class.
    - The dataclasses I am going to return: decided to return custom dataclasses instead of psutil's raw types. This way, if psutil ever changes, only the collector needs updating and nothing else breaks.
    - For `get_disks_statistics`, returning a `DiskResult` dataclass (with `partitions` and `errors` lists) instead of a tuple. It makes the fields named and obvious, and much easier to add fields to later.
    - Look for edge cases: If a partition throws a `PermissionError` or `OSError`, just skip it and append an error message to `DiskResult.errors` instead of crashing. One bad partition shouldn't take down the whole dashboard.
    - Write the main `get_snapshot` function. Everything else will call this to get CPU, memory, and disk stats packed into a single `Snapshot` with a UTC timestamp.

2. Begin writing a test file for collector (`test_collector.py`), to make sure everything works and functions properly
    - Look for edge cases and things that might cause issues across different machines.
    - Research how to use `pytest` and how to mock `psutil` calls.
    - Found out how to mock `psutil` calls via `monkeypatch` so tests never depend on real system state.
    - Begin writing test cases for `get_cpu_utilization` and `get_virtual_memory`. Patch psutil directly and assert that the fields map correctly onto my dataclasses.
    - Write tests for `get_disks_statistics` covering all the edge cases: a single inaccessible partition, all partitions inaccessible, an unmounted partition, and no partitions at all. Test `PermissionError` and `OSError` separately.
    - Write tests for `get_snapshot` by patching the collector functions themselves instead of psutil (since it sits one level higher). Check the happy path and verify that disk errors surface correctly on `Snapshot.errors`.

Begin thinking how the logger file should look like, how it should be structured and what it needs to actually log. Sketch on the side what the logger class will need, how to separate the functions and logic in it.

3. Begin writing the `logger.py` file
    - Decided to create a Logger class, since I want one logger instance running for the program. Each instance shares the same log file.
    - Create `__init__` function, which saves the log path and also checks if the log path is valid, if not the program shouldn't run. You do not want to have it run for hours only to realize the log file was never working.
    - Separate the `log_snapshot` function into multiple functions, each handles different logic. Have a private function named `_snapshot_2_dict` which takes the
    snapshot dataclass passed and converts it to a dict. The other function is `_log_2_file` which handles the I/O aspect of actually writing to the file, and making sure the file exists.
    - Began writing the `_snapshot_2_dict` function, to convert the snapshot to a dict so I can serialize it. I initially began trying to convert it manually, I had issues with serializing the datetime, converteded it to a serializable format. I started trying to use `vars(dataclass)` on each dataclass inside of the snapshot. It initially worked but when I got to a list of dataclasses (the disks) then it stopped working. Tried manually converting it to a dict of lists, but then begain searching online.
    I found `dataclasses.asdict(dataclass)` which does the conversion for me.
    - Began writing `_log_2_file`, decided to open file in append mode to not overwrite any data already written inside of it. Convert the dict to json then append it to the file. Added try except block to catch any unexpected errors, these will be returned to the caller and later on shown in the display.
    - Began writing `log_snapshot` function, a public method to be used to log each time a snapshot is taken. This function calls both `_snapshot_2_dict` and `_log_2_file`. Decided to make `log_snapshot` return `None` if the log was successful, or an error string if it failed. That way instead of having a try except around every log_snapshot call, I can just do a simple if statement.

4. Begin writing a test file for logger (`test_logger.py`) to make sure the module works properly.
    - Think of what needs to be test inside of logger
    - Begin by making a test to make sure that `_snapshot_2_dict` actually converts everything correctly. Also make a test to make sure it still works if disks is empty.
    - Next make tests for the `_log_2_file` function. I made two tests, one that check if the log works and it logged it correctly. And the second test is what happens if it can't write to the file.
    - Now make the tests for `log_snapshot` function. My first test checks if it can write to the file properly and it checks if it wrote the correct data. Second tests is to write to the file twice to make sure nothing gets overwritten. Third test it if the file now causes an error when trying to write to it.
    - I have mocked opening the file and trying to write it in cases where it should cause errors. I initially did it via changing the permission of the file but I thought it was too breakable. Switched to mocking builtins.open directly using unittest.mock.patch, I wasn't sure how os.chmod would perform on different os's.
    - Added multiple tests for the `__init__` function. First test function tries to give an invalid path to make sure an exception gets raised. The second test function checks what happens if the path given is a directory. The third test makes sure that it actually works with a valid path.

Begin researching about `rich` library, how it is used and what I need. Began playing around with the rich library and its tables, layouts and panels.

5. Begin writing `display.py` file
    - Deicded to create a Display class, that way main instantiates display once and calls each of its functions.
    - Began with the `__init__` function, splitting the display into multiple layouts. A top and bottom. Then I split the top into 2, one for CPU metrics and the other for memory metrics. Currently the lower layout is just for disks, but later on will add network statistics to it too.
    - Created `_update_cpu_metrics` function, it creates a table and puts in the value for each core, and a text showing the overall CPU usage percentage. I thought the space looked very empty doing it like this with only two columns, so I decided to split the total cores into tables of 6 cores.
    - Created `_update_memory_metrics` function, which creates a table for the memory metricss.
    - Created `_update_disks_metrics` function, it iterates over every disk and for every disk it adds a row to the table.
    - I decided I should make the bytes appear as either MB or GB since it is hard to understand what the bytes on it own is. I first did only GB but then realized smaller numbers would make sense if they use MB. Created a function `_format_bytes` which decides if to format the bytes in MB or GB.
    - I initially had the help functions (`_format_bytes`, `_bytes_to_gb`, `_bytes_to_mb`) inside the Display class. I decided to move them out since they had no point in being a static method in the class.
    - I then added color coding, I made a function `_get_color` which takes a percentage as a parameter and returns me a rich color name. I use the color coding for usage percentages for CPU, memory and disks.
    - Decided I want to switch `_update_cpu_metrics` function from using multiple tables, and make it use one table with the option to have multiple columns of cores and usages. I think it looks better than way and it seems to resize to different window sizes better too.
    - Updated `_update_disks_metrics` to also show any disk errors below the table as red text, so they dont just silently get ignored in the display.
    - Ran into a small issue where even when there were no errors an empty space was still rendering below the table. Added an `if errors` check before rendering the error text to fix that.

6. Begin writing `main.py` file
    - Decided to write a `run_monitor` function instead of putting everything in main. Takes `interval` and `path` as parameters, and main just handles parsing the args and passing them in. Keeps things cleaner.
    - Used `rich`'s `Live` with `screen=True`. Set `refresh_per_second=4`, wasnt sure what value to pick here but 4 felt smooth enough without being excessive.
    - While testing I noticed the timing felt off, the loop was running slower than the interval I was passing in. Realized the issue was that `cpu_interval` already blocks for the duration of the measurement, so adding `time.sleep` on top of it meant the real cycle time was basically `cpu_interval + sleep`. Removed the sleep entirely.
    - Added a minimum interval check of `0.1` seconds. I tried passing `0` at some point and it just flooded the log file instantly, also psutil was returning the same cached values over and over since it had no time to actually measure anything. Used `parser.error()` to handle it since it shows the usage message and exits, cleaner than raising an exception myself.
