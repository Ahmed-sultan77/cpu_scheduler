import pandas as pd

class Process:
    def __init__(self, pid, arrival_time, burst_time, priority):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority

class SchedulerMetrics:
    @staticmethod
    def calculate_averages(results):
        n = len(results)
        if n == 0: return 0, 0, 0
        avg_wt = sum(p['wt'] for p in results) / n
        avg_tat = sum(p['tat'] for p in results) / n
        avg_rt = sum(p['rt'] for p in results) / n
        return round(avg_wt, 2), round(avg_tat, 2), round(avg_rt, 2)

    @staticmethod
    def display_results(algorithm_name, results):
        print(f"\n--- {algorithm_name} Results Table ---")
        df = pd.DataFrame(results)
        print(df[['pid', 'wt', 'tat', 'rt']].to_string(index=False))
        return SchedulerMetrics.calculate_averages(results)

def run_sjf_non_preemptive(processes):
    procs = [Process(p.pid, p.arrival_time, p.burst_time, p.priority) for p in processes]
    n = len(procs)
    current_time, completed = 0, 0
    is_completed = [False] * n
    results = []

    while completed < n:
        available = [(i, procs[i]) for i in range(n) if procs[i].arrival_time <= current_time and not is_completed[i]]
        if available:
            idx, p = min(available, key=lambda x: x[1].burst_time)
            start_time = current_time
            finish_time = start_time + p.burst_time
            results.append({
                'pid': p.pid, 
                'wt': start_time - p.arrival_time, 
                'tat': finish_time - p.arrival_time, 
                'rt': start_time - p.arrival_time
            })
            current_time = finish_time
            is_completed[idx] = True
            completed += 1
        else:
            current_time += 1
    return results

def run_priority_non_preemptive(processes):
    procs = [Process(p.pid, p.arrival_time, p.burst_time, p.priority) for p in processes]
    n = len(procs)
    current_time, completed = 0, 0
    is_completed = [False] * n
    results = []

    while completed < n:
        available = [(i, procs[i]) for i in range(n) if procs[i].arrival_time <= current_time and not is_completed[i]]
        if available:
            idx, p = min(available, key=lambda x: (x[1].priority, x[1].arrival_time))
            start_time = current_time
            finish_time = start_time + p.burst_time
            results.append({
                'pid': p.pid, 
                'wt': start_time - p.arrival_time, 
                'tat': finish_time - p.arrival_time, 
                'rt': start_time - p.arrival_time
            })
            current_time = finish_time
            is_completed[idx] = True
            completed += 1
        else:
            current_time += 1
    return results

test_processes = [
    Process(pid=1, arrival_time=0, burst_time=10, priority=1),
    Process(pid=2, arrival_time=0, burst_time=2, priority=5),
    Process(pid=3, arrival_time=2, burst_time=4, priority=2)
]

sjf_res = run_sjf_non_preemptive(test_processes)
pri_res = run_priority_non_preemptive(test_processes)

sjf_avg = SchedulerMetrics.display_results("SJF (Non-Preemptive)", sjf_res)
pri_avg = SchedulerMetrics.display_results("Priority (Non-Preemptive)", pri_res)

print("\n--- Final Comparison ---")
print(f"SJF Avg WT: {sjf_avg[0]}, Avg TAT: {sjf_avg[1]}")
print(f"Priority Avg WT: {pri_avg[0]}, Avg TAT: {pri_avg[1]}")
