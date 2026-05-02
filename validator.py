from __future__ import annotations
from typing import NamedTuple

class ValidationResult(NamedTuple):
    is_valid: bool
    error_message: str
    parsed_data: dict

MIN_ARRIVAL_TIME: int = 0
MIN_BURST_TIME:   int = 1
MIN_PRIORITY: int = 1
MAX_PRIORITY: int = 10
MAX_PROCESSES:  int = 10
MIN_PROCESSES: int = 2

def _validate_single_row(row: dict, row_index: int) -> ValidationResult:
    label = f"Row {row_index}"
    required_fields = ("pid", "arrival_time", "burst_time", "priority")

    for field_name in required_fields:
        raw_value = row.get(field_name, "").strip()
        if not raw_value:
            return ValidationResult(
                is_valid=False,
                error_message=f"{label}: The field '{field_name}' is empty.\nAll four fields are required for every process.",
                parsed_data={},
            )

    raw_pid = row["pid"].strip()
    raw_arrival  = row["arrival_time"].strip()
    raw_burst = row["burst_time"].strip()
    raw_priority = row["priority"].strip()

    if " " in raw_pid:
        return ValidationResult(
            is_valid=False,
            error_message=f"{label}: Process ID '{raw_pid}' contains a space.\nPIDs must be single words, e.g. 'P1', 'P2'.",
            parsed_data={},
        )

    try:
        arrival_time = int(raw_arrival)
    except ValueError:
        return ValidationResult(
            is_valid=False,
            error_message=f"{label} (PID='{raw_pid}'): Arrival Time '{raw_arrival}' is not a valid integer.",
            parsed_data={},
        )

    if arrival_time < MIN_ARRIVAL_TIME:
        return ValidationResult(
            is_valid=False,
            error_message=f"{label} (PID='{raw_pid}'): Arrival Time cannot be negative.",
            parsed_data={},
        )

    try:
        burst_time = int(raw_burst)
    except ValueError:
        return ValidationResult(
            is_valid=False,
            error_message=f"{label} (PID='{raw_pid}'): Burst Time '{raw_burst}' is not a valid integer.",
            parsed_data={},
        )

    if burst_time < MIN_BURST_TIME:
        return ValidationResult(
            is_valid=False,
            error_message=f"{label} (PID='{raw_pid}'): Burst Time must be at least {MIN_BURST_TIME}.",
            parsed_data={},
        )

    try:
        priority = int(raw_priority)
    except ValueError:
        return ValidationResult(
            is_valid=False,
            error_message=f"{label} (PID='{raw_pid}'): Priority '{raw_priority}' is not a valid integer.",
            parsed_data={},
        )

    if not (MIN_PRIORITY <= priority <= MAX_PRIORITY):
        return ValidationResult(
            is_valid=False,
            error_message=f"{label} (PID='{raw_pid}'): Priority {priority} is out of range ({MIN_PRIORITY}-{MAX_PRIORITY}).",
            parsed_data={},
        )

    clean_process = {
        "pid":  raw_pid,
        "arrival_time": arrival_time,
        "burst_time":   burst_time,
        "priority":  priority,
    }

    return ValidationResult(is_valid=True, error_message="", parsed_data={"process": clean_process})

class Validator:
    @staticmethod
    def validate_all(rows: list[dict]) -> ValidationResult:
        if not isinstance(rows, list):
            return ValidationResult(False, "Internal error: input must be a list.", {})

        num_rows = len(rows)
        if num_rows < MIN_PROCESSES:
            return ValidationResult(False, f"Minimum required processes: {MIN_PROCESSES}.", {})
        if num_rows > MAX_PROCESSES:
            return ValidationResult(False, f"Maximum allowed processes: {MAX_PROCESSES}.", {})

        clean_processes: list[dict] = []
        for index, row in enumerate(rows, start=1):
            row_result = _validate_single_row(row, row_index=index)
            if not row_result.is_valid:
                return row_result
            clean_processes.append(row_result.parsed_data["process"])

        seen_pids: set[str] = set()
        duplicate_pids: list[str] = []
        for proc in clean_processes:
            pid = proc["pid"]
            if pid in seen_pids:
                duplicate_pids.append(pid)
            else:
                seen_pids.add(pid)

        if duplicate_pids:
            return ValidationResult(False, f"Duplicate Process ID(s) found: {', '.join(duplicate_pids)}.", {})

        return ValidationResult(True, "", {"processes": clean_processes})

    @staticmethod
    def validate_single_process(row: dict, row_index: int = 1) -> ValidationResult:
        result = _validate_single_row(row, row_index)
        if not result.is_valid:
            return result
        return ValidationResult(True, "", {"processes": [result.parsed_data["process"]]})

if __name__ == "__main__":
    pass