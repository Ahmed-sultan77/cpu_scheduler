from __future__ import annotations
import sys
import os
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Process

@dataclass
class AlgorithmResult:
    algorithm_name: str
    processes: list[Process]
    gantt: list
    avg_waiting_time: float
    avg_turnaround_time: float
    avg_response_time: float

    def process_rows(self) -> list[dict]:
        return [p.summary_dict() for p in self.processes]

    def averages_dict(self) -> dict:
        return {
            "algorithm": self.algorithm_name,
            "avg_waiting_time": self.avg_waiting_time,
            "avg_turnaround_time": self.avg_turnaround_time,
            "avg_response_time": self.avg_response_time,
        }

    def __str__(self) -> str:
        header = f"=== {self.algorithm_name} Results ==="
        rows = [
            f" {p.pid:6s}  WT={p.waiting_time:3d}  TAT={p.turnaround_time:3d}  RT={p.response_time:3d}"
            for p in self.processes
        ]
        summary = (
            f"  Avg WT={self.avg_waiting_time:.2f}  "
            f"Avg TAT={self.avg_turnaround_time:.2f}  "
            f"Avg RT={self.avg_response_time:.2f}"
        )
        return "\n".join([header] + rows + [summary])

def calculate(algorithm_output: dict, algorithm_name: str) -> AlgorithmResult:
    processes: list[Process] = algorithm_output["processes"]
    gantt = algorithm_output["gantt"]

    if not processes:
        raise ValueError(
            f"[{algorithm_name}] calculate() received an empty process list."
        )

    for process in processes:
        process.calculate_metrics()

    n = len(processes)
    avg_wt  = sum(p.waiting_time for p in processes) / n
    avg_tat = sum(p.turnaround_time for p in processes) / n
    avg_rt  = sum(p.response_time for p in processes) / n

    return AlgorithmResult(
        algorithm_name=algorithm_name,
        processes=processes,
        gantt=gantt,
        avg_waiting_time=round(avg_wt, 2),
        avg_turnaround_time=round(avg_tat, 2),
        avg_response_time=round(avg_rt, 2),
    )

if __name__ == "__main__":
    pass