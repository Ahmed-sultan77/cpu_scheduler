from __future__ import annotations
from typing import NamedTuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Process, UNSET

class GanttEntry(NamedTuple):
    pid: str
    start: int
    end: int

def _select_process(ready_queue: list[Process]) -> Process | None:
    if not ready_queue:
        return None

    return min(
        ready_queue,
        key=lambda p: (
            p.remaining_time,
            p.arrival_time,
            p.pid,
        ),
    )

def _compress_gantt(raw_gantt: list[str], start_offset: int = 0) -> list[GanttEntry]:
    if not raw_gantt:
        return []

    compressed: list[GanttEntry] = []
    block_pid = raw_gantt[0]
    block_start = start_offset

    for tick_index, current_pid in enumerate(raw_gantt[1:], start=1):
        if current_pid != block_pid:
            compressed.append(GanttEntry(
                pid=block_pid,
                start=block_start,
                end=start_offset + tick_index,
            ))
            block_pid = current_pid
            block_start = start_offset + tick_index

    compressed.append(GanttEntry(
        pid=block_pid,
        start=block_start,
        end=start_offset + len(raw_gantt),
    ))

    return compressed

def run_sjf(processes: list[Process]) -> dict:
    if not processes or not isinstance(processes, list):
        raise ValueError(
            "run_sjf() received an empty or invalid process list."
        )

    simulation_start: int = min(p.arrival_time for p in processes)
    simulation_end_bound: int = (
        max(p.arrival_time for p in processes)
        + sum(p.burst_time for p in processes)
        + 1
    )

    raw_gantt: list[str] = []
    current_time: int = simulation_start
    finished_count: int = 0
    total_processes: int = len(processes)

    while finished_count < total_processes:
        if current_time > simulation_end_bound:
            raise RuntimeError(
                f"SJF simulation exceeded safety bound at t={current_time}. "
                "Check for processes with burst_time=0 or duplicate state."
            )

        ready_queue: list[Process] = [
            p for p in processes
            if p.arrival_time <= current_time and p.remaining_time > 0
        ]

        chosen: Process | None = _select_process(ready_queue)

        if chosen is None:
            raw_gantt.append("idle")
            current_time += 1
            continue

        if chosen.start_time == UNSET:
            chosen.start_time = current_time

        chosen.remaining_time -= 1
        raw_gantt.append(chosen.pid)
        current_time += 1

        if chosen.remaining_time == 0:
            chosen.completion_time = current_time
            finished_count += 1

    gantt_chart: list[GanttEntry] = _compress_gantt(raw_gantt, start_offset=simulation_start)

    return {
        "processes": processes,
        "gantt": gantt_chart,
    }