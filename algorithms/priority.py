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

    # lower priority number = higher priority
    return min(
        ready_queue,
        key=lambda p: (
            p.priority,
            p.arrival_time,
            p.pid,
        ),
    )


def _compress_gantt(raw_gantt: list[str], start_offset: int = 0) -> list[GanttEntry]:
    if not raw_gantt:
        return []

    compressed = []
    current_pid = raw_gantt[0]
    start = start_offset

    for i, pid in enumerate(raw_gantt[1:], start=1):
        if pid != current_pid:
            compressed.append(GanttEntry(current_pid, start, start_offset + i))
            current_pid = pid
            start = start_offset + i

    compressed.append(GanttEntry(current_pid, start, start_offset + len(raw_gantt)))
    return compressed


def run_priority(processes: list[Process]) -> dict:
    if not processes:
        raise ValueError("Empty process list")

    current_time = 0
    end_bound = max(p.arrival_time for p in processes) + sum(p.burst_time for p in processes) + 1

    raw_gantt = []
    finished = 0
    total = len(processes)

    while finished < total:
        if current_time > end_bound:
            raise RuntimeError("Simulation exceeded limit")

        ready_queue = [
            p for p in processes
            if p.arrival_time <= current_time and p.remaining_time > 0
        ]

        chosen = _select_process(ready_queue)

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
            finished += 1

    gantt = _compress_gantt(raw_gantt, start_offset=0)

    return {
        "processes": processes,
        "gantt": gantt,
    }