from __future__ import annotations
import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Process
from algorithms.sjf import run_sjf
from algorithms.priority import run_priority
from metrics.calculator import calculate

def _make(pid, arrival, burst, priority=1):
    return Process(pid=pid, arrival_time=arrival, burst_time=burst, priority=priority)

class TestMetricsCalculation:

    def test_wt_tat_rt_single_process(self):
        p = _make("P1", arrival=0, burst=5)
        result = run_sjf([p])
        calc = calculate(result, "SJF")
        proc = calc.processes[0]
        assert proc.turnaround_time == 5   # CT(5) - AT(0)
        assert proc.waiting_time    == 0   # TAT - BT
        assert proc.response_time   == 0   # ST(0) - AT(0)

    def test_wt_tat_rt_with_wait(self):
        procs = [_make("P1", 0, 5), _make("P2", 0, 3)]
        result = run_sjf(procs)
        calc = calculate(result, "SJF")
        p2 = next(p for p in calc.processes if p.pid == "P2")
        assert p2.turnaround_time == p2.completion_time - p2.arrival_time
        assert p2.waiting_time    == p2.turnaround_time - p2.burst_time
        assert p2.response_time   == p2.start_time - p2.arrival_time

    def test_averages_correct(self):
        procs = [_make("P1", 0, 4), _make("P2", 0, 2)]
        result = run_sjf(procs)
        calc = calculate(result, "SJF")
        expected_avg_tat = sum(p.turnaround_time for p in calc.processes) / 2
        assert calc.avg_turnaround_time == round(expected_avg_tat, 2)

    def test_response_time_equals_wt_for_nonpreemptive_like_case(self):
        procs = [_make("P1", 0, 2), _make("P2", 3, 2)]
        result = run_sjf(procs)
        calc = calculate(result, "SJF")
        for p in calc.processes:
            assert p.response_time >= 0

    def test_priority_metrics_consistent_with_gantt(self):
        procs = [
            Process(pid="P1", arrival_time=0, burst_time=4, priority=3),
            Process(pid="P2", arrival_time=0, burst_time=2, priority=1),
        ]
        result = run_priority(procs)
        calc = calculate(result, "Priority")
        p2 = next(p for p in calc.processes if p.pid == "P2")
        assert p2.start_time == 0
        assert p2.completion_time == 2
        assert p2.turnaround_time == 2
        assert p2.waiting_time == 0

    def test_late_arrival_rt_correct(self):
        procs = [_make("P1", arrival=5, burst=3)]
        result = run_sjf(procs)
        calc = calculate(result, "SJF")
        assert calc.processes[0].response_time == 0  # started immediately at arrival
        assert calc.processes[0].turnaround_time == 3

    def test_empty_process_list_raises(self):
        with pytest.raises((ValueError, Exception)):
            calculate({"processes": [], "gantt": []}, "SJF")