from __future__ import annotations
import sys
import os
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics.calculator import AlgorithmResult

STARVATION_MULTIPLIER: float = 2.5

@dataclass
class MetricComparison:
    metric_name: str
    sjf_value: float
    priority_value: float
    winner: str
    difference: float
    is_tie: bool

@dataclass
class ComparisonReport:
    metrics: list[MetricComparison]
    starved_in_sjf: list[str]
    starved_in_priority: list[str]
    overall_winner: str
    summary_lines: list[str]
    conclusion_lines: list[str]
    recommendation: str
    sjf_better_wt: bool
    sjf_better_tat: bool
    sjf_better_rt: bool

    def as_dict(self) -> dict:
        return {
            "overall_winner": self.overall_winner,
            "metrics": [
                {
                    "metric": m.metric_name,
                    "sjf": m.sjf_value,
                    "priority": m.priority_value,
                    "winner": m.winner,
                    "difference": m.difference,
                    "is_tie": m.is_tie,
                }
                for m in self.metrics
            ],
            "starved_in_sjf": self.starved_in_sjf,
            "starved_in_priority": self.starved_in_priority,
            "recommendation": self.recommendation,
        }

def _compare_metric(name: str, sjf_val: float, pri_val: float, sjf_name: str, pri_name: str) -> MetricComparison:
    diff = round(abs(sjf_val - pri_val), 2)
    is_tie = diff == 0.0
    if is_tie:
        winner = "Tie"
    elif sjf_val < pri_val:
        winner = sjf_name
    else:
        winner = pri_name
    return MetricComparison(
        metric_name=name,
        sjf_value=sjf_val,
        priority_value=pri_val,
        winner=winner,
        difference=diff,
        is_tie=is_tie,
    )

def _detect_starvation(result: AlgorithmResult) -> list[str]:
    avg_wt = result.avg_waiting_time
    if avg_wt <= 0:
        return []
    threshold = STARVATION_MULTIPLIER * avg_wt
    return [p.pid for p in result.processes if p.waiting_time >= threshold]

def _build_summary_lines(metrics: list[MetricComparison], sjf_name: str, pri_name: str, starved_sjf: list[str], starved_pri: list[str]) -> list[str]:
    lines: list[str] = []
    for m in metrics:
        if m.is_tie:
            verdict = "Both algorithms tied"
        else:
            verdict = f"{m.winner} is better (by {m.difference:.2f})"
        lines.append(f"{m.metric_name}: {sjf_name} = {m.sjf_value:.2f}  |  {pri_name} = {m.priority_value:.2f}  →  {verdict}")
    lines.append("")
    if starved_sjf:
        pids = ", ".join(starved_sjf)
        lines.append(f"Fairness warning ({sjf_name}): Process(es) {pids} waited significantly longer than average. Possible starvation risk.")
    else:
        lines.append(f"Fairness ({sjf_name}): No starvation detected.")
    if starved_pri:
        pids = ", ".join(starved_pri)
        lines.append(f"Fairness warning ({pri_name}): Process(es) {pids} waited significantly longer than average. Possible starvation risk.")
    else:
        lines.append(f"Fairness ({pri_name}): No starvation detected.")
    return lines

def _build_conclusion_lines(metrics: list[MetricComparison], sjf_name: str, pri_name: str, overall_winner: str, starved_sjf: list[str], starved_pri: list[str]) -> list[str]:
    lines: list[str] = []
    wt_cmp  = next(m for m in metrics if "Waiting" in m.metric_name)
    tat_cmp = next(m for m in metrics if "Turnaround" in m.metric_name)
    rt_cmp  = next(m for m in metrics if "Response" in m.metric_name)
    lines.append(f"Average Waiting Time: {wt_cmp.winner} achieved a lower value ({wt_cmp.sjf_value:.2f} vs {wt_cmp.priority_value:.2f})." if not wt_cmp.is_tie else f"Average Waiting Time: Both algorithms performed equally ({wt_cmp.sjf_value:.2f}).")
    lines.append(f"Average Turnaround Time: {tat_cmp.winner} achieved a lower value ({tat_cmp.sjf_value:.2f} vs {tat_cmp.priority_value:.2f})." if not tat_cmp.is_tie else f"Average Turnaround Time: Both algorithms performed equally ({tat_cmp.sjf_value:.2f}).")
    lines.append(f"{sjf_name} selects the process with the shortest remaining burst time, so short jobs are consistently executed first, reducing their waiting time. Long jobs with low priority may experience delay under {sjf_name}.")
    lines.append(f"{pri_name} always selects the highest-priority (lowest priority number) available process. Urgent processes receive CPU time ahead of longer, lower-priority ones, even if those are shorter.")
    if starved_sjf or starved_pri:
        affected = []
        if starved_sjf: affected.append(f"{sjf_name} (PIDs: {', '.join(starved_sjf)})")
        if starved_pri: affected.append(f"{pri_name} (PIDs: {', '.join(starved_pri)})")
        lines.append(f"Unfair delay was observed under: {'; '.join(affected)}. Aging or a combined policy could mitigate this in practice.")
    else:
        lines.append("No significant starvation was detected under either algorithm for this workload.")
    lines.append(f"Trade-off — Efficiency vs Urgency: {sjf_name} optimises for throughput and minimises average waiting time but ignores process importance. {pri_name} ensures critical processes are served promptly but may delay short low-priority jobs, potentially increasing average WT.")
    sjf_wins = sum(1 for m in metrics if m.winner == sjf_name)
    pri_wins = sum(1 for m in metrics if m.winner == pri_name)
    if overall_winner == sjf_name:
        lines.append(f"Recommendation: {sjf_name} performed better on this dataset, winning {sjf_wins}/3 metrics. It is recommended when throughput and average waiting time are the priority criteria.")
    elif overall_winner == pri_name:
        lines.append(f"Recommendation: {pri_name} performed better on this dataset, winning {pri_wins}/3 metrics. It is recommended when serving urgent or time-critical processes is more important than minimising average waiting time.")
    else:
        lines.append(f"Recommendation: Both algorithms performed equally across all metrics on this workload. Choose {sjf_name} if throughput matters most, or {pri_name} if urgency and process importance drive the scheduling policy.")
    return lines

def compare(sjf_result: AlgorithmResult, priority_result: AlgorithmResult) -> ComparisonReport:
    sjf_name = sjf_result.algorithm_name
    pri_name = priority_result.algorithm_name
    wt_cmp = _compare_metric("Average Waiting Time", sjf_result.avg_waiting_time, priority_result.avg_waiting_time, sjf_name, pri_name)
    tat_cmp = _compare_metric("Average Turnaround Time", sjf_result.avg_turnaround_time, priority_result.avg_turnaround_time, sjf_name, pri_name)
    rt_cmp = _compare_metric("Average Response Time", sjf_result.avg_response_time, priority_result.avg_response_time, sjf_name, pri_name)
    metrics = [wt_cmp, tat_cmp, rt_cmp]
    starved_sjf = _detect_starvation(sjf_result)
    starved_pri = _detect_starvation(priority_result)
    sjf_wins = sum(1 for m in metrics if m.winner == sjf_name)
    pri_wins = sum(1 for m in metrics if m.winner == pri_name)
    if sjf_wins > pri_wins:
        overall_winner = sjf_name
    elif pri_wins > sjf_wins:
        overall_winner = pri_name
    else:
        overall_winner = "Tie"
    summary_lines = _build_summary_lines(metrics, sjf_name, pri_name, starved_sjf, starved_pri)
    conclusion_lines = _build_conclusion_lines(metrics, sjf_name, pri_name, overall_winner, starved_sjf, starved_pri)
    if overall_winner == sjf_name:
        recommendation = f"{sjf_name} is recommended: it achieved better average metrics for this workload ({sjf_wins}/3 metrics won)."
    elif overall_winner == pri_name:
        recommendation = f"{pri_name} is recommended: it served urgent processes faster and achieved better overall metrics ({pri_wins}/3 metrics won)."
    else:
        recommendation = "Both algorithms are equally suited to this workload; choose based on whether throughput (SJF) or urgency (Priority) matters more for your use case."
    return ComparisonReport(
        metrics=metrics,
        starved_in_sjf=starved_sjf,
        starved_in_priority=starved_pri,
        overall_winner=overall_winner,
        summary_lines=summary_lines,
        conclusion_lines=conclusion_lines,
        recommendation=recommendation,
        sjf_better_wt=(wt_cmp.winner == sjf_name),
        sjf_better_tat=(tat_cmp.winner == sjf_name),
        sjf_better_rt=(rt_cmp.winner == sjf_name),
    )

if __name__ == "__main__":
    pass