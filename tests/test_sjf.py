from __future__ import annotations

import copy
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Process, UNSET
from algorithms.sjf import run_sjf


def _make(pid: str, arrival: int, burst: int, priority: int = 1) -> Process:
    return Process(pid=pid, arrival_time=arrival, burst_time=burst, priority=priority)


def _gantt_pids(result: dict) -> list[str]:
    return [entry.pid for entry in result["gantt"]]


def _gantt_spans(result: dict) -> list[tuple[str, int, int]]:
    return [(e.pid, e.start, e.end) for e in result["gantt"]]


def _pid_completion(result: dict, pid: str) -> int:
    proc = next(p for p in result["processes"] if p.pid == pid)
    return proc.completion_time


@pytest.fixture
def basic_processes() -> list[Process]:
    return [
        _make("P1", arrival=0, burst=6),
        _make("P2", arrival=1, burst=3),
        _make("P3", arrival=2, burst=8),
        _make("P4", arrival=3, burst=2),
        _make("P5", arrival=5, burst=4),
    ]


@pytest.fixture
def burst_conflict_processes() -> list[Process]:
    return [
        _make("P1", arrival=0, burst=10),
        _make("P2", arrival=1, burst=2),
        _make("P3", arrival=3, burst=4),
    ]


@pytest.fixture
def starvation_processes() -> list[Process]:
    return [
        _make("P1", arrival=0, burst=2),
        _make("P2", arrival=0, burst=2),
        _make("P3", arrival=0, burst=2),
        _make("P4", arrival=0, burst=20),
        _make("P5", arrival=2, burst=3),
    ]


class TestSJFBasicCorrectness:

    def test_all_processes_complete(self, basic_processes):
        result = run_sjf(basic_processes)
        for p in result["processes"]:
            assert p.completion_time != UNSET, f"{p.pid} never completed"

    def test_completion_time_after_arrival(self, basic_processes):
        result = run_sjf(basic_processes)
        for p in result["processes"]:
            assert p.completion_time > p.arrival_time

    def test_completion_time_not_before_burst_done(self, basic_processes):
        result = run_sjf(basic_processes)
        for p in result["processes"]:
            assert p.completion_time - p.arrival_time >= p.burst_time

    def test_gantt_covers_all_burst_time(self, basic_processes):
        result = run_sjf(basic_processes)
        total_burst = sum(p.burst_time for p in basic_processes)
        cpu_time = sum(
            e.end - e.start
            for e in result["gantt"]
            if e.pid != "idle"
        )
        assert cpu_time == total_burst

    def test_result_contains_required_keys(self, basic_processes):
        result = run_sjf(basic_processes)
        assert "processes" in result
        assert "gantt" in result

    def test_start_time_set_for_all_processes(self, basic_processes):
        result = run_sjf(basic_processes)
        for p in result["processes"]:
            assert p.start_time != UNSET, f"{p.pid} has no start_time"

    def test_start_time_not_before_arrival(self, basic_processes):
        result = run_sjf(basic_processes)
        for p in result["processes"]:
            assert p.start_time >= p.arrival_time


class TestSJFPreemption:

    def test_short_job_preempts_long_job(self, burst_conflict_processes):
        result = run_sjf(burst_conflict_processes)
        pids = _gantt_pids(result)
        p2_last = max(i for i, pid in enumerate(pids) if pid == "P2")
        p1_last = max(i for i, pid in enumerate(pids) if pid == "P1")
        assert p2_last < p1_last

    def test_preempted_process_still_completes(self, burst_conflict_processes):
        result = run_sjf(burst_conflict_processes)
        for p in result["processes"]:
            assert p.remaining_time == 0

    def test_p2_completes_before_p1_in_conflict_scenario(self, burst_conflict_processes):
        result = run_sjf(burst_conflict_processes)
        ct_p1 = _pid_completion(result, "P1")
        ct_p2 = _pid_completion(result, "P2")
        assert ct_p2 < ct_p1

    def test_gantt_shows_p1_then_p2_then_p1(self, burst_conflict_processes):
        result = run_sjf(burst_conflict_processes)
        pids = _gantt_pids(result)
        assert pids[0] == "P1"
        assert "P2" in pids
        p1_indices = [i for i, p in enumerate(pids) if p == "P1"]
        assert len(p1_indices) >= 2


class TestSJFArrivalHandling:

    def test_idle_inserted_when_no_process_available(self):
        processes = [_make("P1", arrival=5, burst=3)]
        result = run_sjf(processes)
        pids = _gantt_pids(result)
        assert "idle" in pids

    def test_idle_ends_when_process_arrives(self):
        processes = [_make("P1", arrival=5, burst=3)]
        result = run_sjf(processes)
        spans = _gantt_spans(result)
        idle_block = next(s for s in spans if s[0] == "idle")
        assert idle_block[2] == 5

    def test_no_idle_when_process_arrives_at_zero(self):
        processes = [_make("P1", arrival=0, burst=4)]
        result = run_sjf(processes)
        pids = _gantt_pids(result)
        assert "idle" not in pids

    def test_late_arriving_process_waits_correctly(self):
        processes = [
            _make("P1", arrival=0, burst=6),
            _make("P2", arrival=10, burst=2),
        ]
        result = run_sjf(processes)
        ct_p1 = _pid_completion(result, "P1")
        ct_p2 = _pid_completion(result, "P2")
        assert ct_p1 == 6
        assert ct_p2 == 12


class TestSJFTieBreaking:

    def test_tie_broken_by_arrival_time(self):
        processes = [
            _make("P1", arrival=0, burst=4),
            _make("P2", arrival=2, burst=4),
        ]
        result = run_sjf(processes)
        pids = _gantt_pids(result)
        assert pids[0] == "P1"

    def test_tie_broken_by_pid_when_arrival_equal(self):
        processes = [
            _make("P2", arrival=0, burst=3),
            _make("P1", arrival=0, burst=3),
        ]
        result = run_sjf(processes)
        pids = _gantt_pids(result)
        assert pids[0] == "P1"


class TestSJFSingleProcess:

    def test_single_process_completes(self):
        processes = [_make("P1", arrival=0, burst=5)]
        result = run_sjf(processes)
        p = result["processes"][0]
        assert p.completion_time == 5
        assert p.start_time == 0
        assert p.remaining_time == 0

    def test_single_process_gantt_has_one_entry(self):
        processes = [_make("P1", arrival=0, burst=5)]
        result = run_sjf(processes)
        non_idle = [e for e in result["gantt"] if e.pid != "idle"]
        assert len(non_idle) == 1

    def test_single_process_with_late_arrival(self):
        processes = [_make("P1", arrival=3, burst=4)]
        result = run_sjf(processes)
        p = result["processes"][0]
        assert p.start_time == 3
        assert p.completion_time == 7


class TestSJFInvalidInput:

    def test_empty_list_raises_value_error(self):
        with pytest.raises(ValueError):
            run_sjf([])

    def test_non_list_raises_value_error(self):
        with pytest.raises(ValueError):
            run_sjf(None)


class TestSJFStarvation:

    def test_long_process_completes_despite_short_arrivals(self, starvation_processes):
        result = run_sjf(starvation_processes)
        p4 = next(p for p in result["processes"] if p.pid == "P4")
        assert p4.completion_time != UNSET
        assert p4.remaining_time == 0

    def test_short_processes_finish_before_long_one(self, starvation_processes):
        result = run_sjf(starvation_processes)
        ct = {p.pid: p.completion_time for p in result["processes"]}
        for pid in ("P1", "P2", "P3", "P5"):
            assert ct[pid] < ct["P4"]

    def test_total_completion_time_is_correct(self, starvation_processes):
        result = run_sjf(starvation_processes)
        total_burst = sum(p.burst_time for p in starvation_processes)
        last_ct = max(p.completion_time for p in result["processes"])
        assert last_ct == total_burst


class TestSJFContextSwitches:

    def test_multiple_preemptions_all_processes_complete(self):
        processes = [
            _make("P1", arrival=0, burst=8),
            _make("P2", arrival=1, burst=1),
            _make("P3", arrival=2, burst=1),
            _make("P4", arrival=3, burst=1),
        ]
        result = run_sjf(processes)
        for p in result["processes"]:
            assert p.remaining_time == 0
            assert p.completion_time != UNSET

    def test_gantt_is_contiguous(self, basic_processes):
        result = run_sjf(basic_processes)
        spans = _gantt_spans(result)
        for i in range(len(spans) - 1):
            assert spans[i][2] == spans[i + 1][1], (
                f"Gap between Gantt entry {i} and {i+1}: "
                f"{spans[i]} → {spans[i+1]}"
            )

    def test_gantt_starts_at_simulation_start(self, basic_processes):
        result = run_sjf(basic_processes)
        earliest = min(p.arrival_time for p in basic_processes)
        assert result["gantt"][0].start == earliest