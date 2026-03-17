import json
import dataclasses

from collector import Snapshot

class Logger:
    """
    Responsible for logging snapshots of system statistics to a log file as JSON
    """

    def __init__(self, path: str) -> None:
        """
        Instantiates the logger and keeps the path for the log file

        Args:
            path (str): The path to the log file
        """
        self.log_path = path

        try:
            with open(self.log_path, "a") as fl: pass
        except OSError as e:
            raise OSError(f"Could not open log file at path {self.log_path}: Error {e}")            

    def _snapshot_2_dict(self, snapshot: Snapshot) -> dict:
        """
        Private method, which takes a snapshot of the Snapshot dataclass and converts it to dict

        Convert the datetime to a serializable object

        Args:
            snapshot (Snapshot): The snapshot data from collector

        Returns:
            dict: Snapshot dataclass converted to a dict
        """
        data_dict = dataclasses.asdict(snapshot)
        data_dict["timestamp"] = snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return data_dict

    def _log_2_file(self, snapshot_dict: dict) -> str | None:
        """
        Private method that handles I/O, writes to the log file

        Args:
            snapshot_dict (dict): The snapshot converted to a dict, for ease of converting to JSON
        
        Returns:
            None if wrote to the file successfuly, or an error string if the write failed.
        """
        try:
            with open(self.log_path, "a") as fl:
                fl.write(json.dumps(snapshot_dict) + "\n")
        except OSError as e:
            return f"Couldn't log to file! Error {e}"

    def log_snapshot(self, snapshot: Snapshot) -> str | None:
        """
        Public method that is called when you need to log whenever a snapshot was taken

        Args:
            snapshot (Snapshot): The snapshot data from collector

        Returns:
            None if the snapshot was logged successfully, or an error string if the write failed.
        """
        data_dict = self._snapshot_2_dict(snapshot=snapshot)
        return self._log_2_file(snapshot_dict=data_dict)
