from __future__ import annotations

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Process, UNSET
from algorithms.priority import run_priority


def _make(pid: str, arrival: int, burst: int, priority: int) -> Process:
    return Process(pid=pid, arrival_time=arrival, burst_time=burst, priority=priority)


def _gantt_pids(result: dict) -> list[str]:
    return [entry.pid for entry in result["gantt"]]


def _gantt_spans(result: dict) -> list[tuple[str, int, int]]:
    return [(e.pid, e.start, e.end) for e in result["gantt"]]


def _completion(result: dict, pid: str) -> int:
    proc = next(p for p in result["processes"] if p.pid == pid)
    return proc.completion_time


def _start(result: dict, pid: str) -> int:
    proc = next(p for p in result["processes"] if p.pid == pid)
    return proc.start_time


@pytest.fixture
def basic_priority_processes() -> list[Process]:
    return [
        _make("P1", arrival=0, burst=6, priority=3),
        _make("P2", arrival=1, burst=3, priority=5),
        _make("P3", arrival=2, burst=8, priority=1),
        _make("P4", arrival=3, burst=2, priority=4),
        _make("P5", arrival=5, burst=4, priority=2),
    ]


@pytest.fixture
def conflict_processes() -> list[Process]:
    return [
        _make("P1", arrival=0, burst=2,  priority=5),
        _make("P2", arrival=0, burst=10, priority=1),
        _make("P3", arrival=1, burst=4,  priority=3),
        _make("P4", arrival=2, burst=1,  priority=4),
        _make("P5", arrival=3, burst=6,  priority=2),
    ]


@pytest.fixture
def starvation_processes() -> list[Process]:
    return [
        _make("P1", arrival=0, burst=2,  priority=1),
        _make("P2", arrival=0, burst=2,  priority=1),
        _make("P3", arrival=0, burst=2,  priority=1),
        _make("P4", arrival=0, burst=20, priority=5),
        _make("P5", arrival=2, burst=3,  priority=2),
    ]


class TestPriorityBasicCorrectness:

    def test_all_processes_complete(self, basic_priority_processes):
        result = run_priority(basic_priority_processes)
        for p in result["processes"]:
            assert p.completion_time != UNSET, f"{p.pid} never completed"

    def test_remaining_time_zero_for_all(self, basic_priority_processes):
        result = run_priority(basic_priority_processes)
        for p in result["processes"]:
            assert p.remaining_time == 0

    def test_completion_time_after_arrival(self, basic_priority_processes):
        result = run_priority(basic_priority_processes)
        for p in result["processes"]:
            assert p.completion_time > p.arrival_time

    def test_completion_time_accounts_for_burst(self, basic_priority_processes):
        result = run_priority(basic_priority_processes)
        for p in result["processes"]:
            assert p.completion_time - p.arrival_time >= p.burst_time

    def test_result_has_required_keys(self, basic_priority_processes):
        result = run_priority(basic_priority_processes)
        assert "processes" in result
        assert "gantt" in result

    def test_start_time_not_before_arrival(self, basic_priority_processes):
        result = run_priority(basic_priority_processes)
        for p in result["processes"]:
            assert p.start_time >= p.arrival_time

    def test_gantt_total_cpu_equals_total_burst(self, basic_priority_processes):
        result = run_priority(basic_priority_processes)
        total_burst = sum(p.burst_time for p in basic_priority_processes)
        cpu_time = sum(
            e.end - e.start for e in result["gantt"] if e.pid != "idle"
        )
        assert cpu_time == total_burst


class TestPrioritySelection:

    def test_highest_priority_runs_first_among_simultaneous_arrivals(self):
        processes = [
            _make("P1", arrival=0, burst=4, priority=3),
            _make("P2", arrival=0, burst=4, priority=1),
        ]
        result = run_priority(processes)
        pids = _gantt_pids(result)
        assert pids[0] == "P2"

    def test_lower_priority_process_waits_for_higher(self):
        processes = [
            _make("P1", arrival=0, burst=10, priority=5),
            _make("P2", arrival=2, burst=4,  priority=1),
        ]
        result = run_priority(processes)
        ct_p2 = _completion(result, "P2")
        ct_p1 = _completion(result, "P1")
        assert ct_p2 < ct_p1

    def test_conflict_scenario_p2_runs_before_p1(self, conflict_processes):
        result = run_priority(conflict_processes)
        pids = _gantt_pids(result)
        assert pids[0] == "P2"

    def test_conflict_p1_waits_longer_than_p2(self, conflict_processes):
        result = run_priority(conflict_processes)
        ct_p1 = _completion(result, "P1")
        ct_p2 = _completion(result, "P2")
        assert ct_p1 > ct_p2


class TestPriorityPreemption:

    def test_arriving_high_priority_preempts_running_process(self):
        processes = [
            _make("P1", arrival=0, burst=8, priority=3),
            _make("P2", arrival=2, burst=3, priority=1),
        ]
        result = run_priority(processes)
        pids = _gantt_pids(result)
        p2_last  = max(i for i, p in enumerate(pids) if p == "P2")
        p1_last  = max(i for i, p in enumerate(pids) if p == "P1")
        assert p2_last < p1_last

    def test_preempted_process_completes_after_higher_priority_done(self):
        processes = [
            _make("P1", arrival=0, burst=6, priority=3),
            _make("P2", arrival=1, burst=2, priority=1),
        ]
        result = run_priority(processes)
        p1 = next(p for p in result["processes"] if p.pid == "P1")
        p2 = next(p for p in result["processes"] if p.pid == "P2")
        assert p1.remaining_time == 0
        assert p2.remaining_time == 0
        assert p2.completion_time < p1.completion_time

    def test_gantt_shows_interleaving_on_preemption(self):
        processes = [
            _make("P1", arrival=0, burst=8, priority=3),
            _make("P2", arrival=2, burst=2, priority=1),
        ]
        result = run_priority(processes)
        pids = _gantt_pids(result)
        p1_indices = [i for i, p in enumerate(pids) if p == "P1"]
        assert len(p1_indices) >= 2
        p2_index = pids.index("P2")
        assert p1_indices[0] < p2_index < p1_indices[-1]


class TestPriorityTieBreaking:

    def test_tie_same_priority_broken_by_arrival_time(self):
        processes = [
            _make("P1", arrival=0, burst=4, priority=2),
            _make("P2", arrival=2, burst=4, priority=2),
        ]
        result = run_priority(processes)
        pids = _gantt_pids(result)
        assert pids[0] == "P1"

    def test_tie_same_priority_same_arrival_broken_by_pid(self):
        processes = [
            _make("P2", arrival=0, burst=3, priority=2),
            _make("P1", arrival=0, burst=3, priority=2),
        ]
        result = run_priority(processes)
        pids = _gantt_pids(result)
        assert pids[0] == "P1"


class TestPriorityIdleCPU:

    def test_idle_inserted_before_first_arrival(self):
        processes = [_make("P1", arrival=5, burst=3, priority=1)]
        result = run_priority(processes)
        pids = _gantt_pids(result)
        assert "idle" in pids

    def test_idle_ends_exactly_at_first_arrival(self):
        processes = [_make("P1", arrival=5, burst=3, priority=1)]
        result = run_priority(processes)
        spans = _gantt_spans(result)
        idle_block = next(s for s in spans if s[0] == "idle")
        assert idle_block[2] == 5

    def test_no_idle_when_process_at_zero(self):
        processes = [_make("P1", arrival=0, burst=4, priority=1)]
        result = run_priority(processes)
        pids = _gantt_pids(result)
        assert "idle" not in pids

    def test_idle_between_two_non_overlapping_processes(self):
        processes = [
            _make("P1", arrival=0, burst=3, priority=1),
            _make("P2", arrival=8, burst=2, priority=1),
        ]
        result = run_priority(processes)
        spans = _gantt_spans(result)
        idle_spans = [s for s in spans if s[0] == "idle"]
        assert len(idle_spans) >= 1
        assert any(s[1] == 3 and s[2] == 8 for s in idle_spans)


class TestPrioritySingleProcess:

    def test_single_process_completes_correctly(self):
        processes = [_make("P1", arrival=0, burst=5, priority=2)]
        result = run_priority(processes)
        p = result["processes"][0]
        assert p.completion_time == 5
        assert p.start_time == 0
        assert p.remaining_time == 0

    def test_single_late_arriving_process(self):
        processes = [_make("P1", arrival=4, burst=3, priority=1)]
        result = run_priority(processes)
        p = result["processes"][0]
        assert p.start_time == 4
        assert p.completion_time == 7


class TestPriorityInvalidInput:

    def test_empty_list_raises_value_error(self):
        with pytest.raises(ValueError):
            run_priority([])


class TestPriorityStarvation:

    def test_low_priority_process_eventually_completes(self, starvation_processes):
        result = run_priority(starvation_processes)
        p4 = next(p for p in result["processes"] if p.pid == "P4")
        assert p4.completion_time != UNSET
        assert p4.remaining_time == 0

    def test_high_priority_processes_complete_before_low(self, starvation_processes):
        result = run_priority(starvation_processes)
        ct = {p.pid: p.completion_time for p in result["processes"]}
        for pid in ("P1", "P2", "P3", "P5"):
            assert ct[pid] < ct["P4"]

    def test_p4_waits_significantly_longer(self, starvation_processes):
        result = run_priority(starvation_processes)
        from metrics.calculator import calculate
        result_copy = calculate(
            {"processes": result["processes"], "gantt": result["gantt"]},
            algorithm_name="Priority",
        )
        p4_wt = next(p.waiting_time for p in result_copy.processes if p.pid == "P4")
        other_wts = [p.waiting_time for p in result_copy.processes if p.pid != "P4"]
        assert p4_wt > max(other_wts)


class TestPriorityGanttIntegrity:

    def test_gantt_is_contiguous(self, basic_priority_processes):
        result = run_priority(basic_priority_processes)
        spans = _gantt_spans(result)
        for i in range(len(spans) - 1):
            assert spans[i][2] == spans[i + 1][1], (
                f"Gap detected between Gantt block {i} and {i+1}: "
                f"{spans[i]} → {spans[i+1]}"
            )

    def test_gantt_starts_at_earliest_arrival(self, basic_priority_processes):
        result = run_priority(basic_priority_processes)
        earliest = min(p.arrival_time for p in basic_priority_processes)
        assert result["gantt"][0].start == earliest

    def test_gantt_ends_at_last_completion(self, basic_priority_processes):
        result = run_priority(basic_priority_processes)
        last_ct = max(p.completion_time for p in result["processes"])
        assert result["gantt"][-1].end == last_ct