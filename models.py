from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

UNSET: int = -1

@dataclass
class Process:
    pid: str = field(metadata={"help": "Unique process ID"})
    arrival_time: int = field(metadata={"help": "Arrival time (>= 0)"})
    burst_time: int = field(metadata={"help": "CPU burst duration (> 0)"})
    priority: int = field(metadata={"help": "Priority (lower = higher prio)"})

    remaining_time: int = field(init=False)
    start_time: int = field(init=False, default=UNSET)
    completion_time: int = field(init=False, default=UNSET)

    waiting_time: int = field(init=False, default=0)
    turnaround_time: int = field(init=False, default=0)
    response_time: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self.remaining_time = self.burst_time

    def reset_state(self) -> None:
        self.remaining_time = self.burst_time
        self.start_time = UNSET
        self.completion_time = UNSET
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = 0

    def calculate_metrics(self) -> None:
        if self.completion_time == UNSET:
            raise ValueError(f"[{self.pid}] completion_time has not been set.")
        if self.start_time == UNSET:
            raise ValueError(f"[{self.pid}] start_time has not been set.")

        self.turnaround_time = self.completion_time - self.arrival_time
        self.waiting_time = self.turnaround_time - self.burst_time
        self.response_time = self.start_time - self.arrival_time

    def __repr__(self) -> str:
        return (
            f"Process(pid='{self.pid}', AT={self.arrival_time}, BT={self.burst_time}, "
            f"Pri={self.priority} | RT={self.response_time}, WT={self.waiting_time}, TAT={self.turnaround_time})"
        )

    def summary_dict(self) -> dict:
        return {
            "pid": self.pid,
            "arrival_time": self.arrival_time,
            "burst_time": self.burst_time,
            "priority": self.priority,
            "start_time": self.start_time,
            "completion_time": self.completion_time,
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "response_time": self.response_time,
        }

def create_process_list(raw_rows: list[dict]) -> list[Process]:
    return [
        Process(
            pid=row["pid"],
            arrival_time=row["arrival_time"],
            burst_time=row["burst_time"],
            priority=row["priority"],
        )
        for row in raw_rows
    ]