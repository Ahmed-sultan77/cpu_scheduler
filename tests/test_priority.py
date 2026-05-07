class Process:
    def __init__(self, pid, arrival_time, burst_time, priority):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority

def calculate_metrics(results):
    n = len(results)
    if n == 0:
        return 0, 0
    
    total_wt = 0
    total_tat = 0
    for res in results:
        total_wt += res['wt']
        total_tat += res['tat']
    
    avg_wt = total_wt / n
    avg_tat = total_tat / n
    
    print("\nAverages:")
    print("Average Waiting Time:", round(avg_wt, 2))
    print("Average Turnaround Time:", round(avg_tat, 2))
    return avg_wt, avg_tat

def display_table(algorithm_name, results):
    print("\n--- " + algorithm_name + " Results Table ---")
    print("PID\tArrival\tBurst\tPriority\tWT\tTAT")
    for res in results:
        print(f"{res['pid']}\t{res['arrival']}\t{res['burst']}\t{res['prio']}\t\t{res['wt']}\t{res['tat']}")
    return calculate_metrics(results)

def run_sjf(processes_list):
    procs = []
    for p in processes_list:
        procs.append(Process(p.pid, p.arrival_time, p.burst_time, p.priority))
    
    n = len(procs)
    current_time = 0
    completed = 0
    is_completed = [False] * n
    results = []

    while completed < n:
        available_indices = []
        for i in range(n):
            if procs[i].arrival_time <= current_time and is_completed[i] == False:
                available_indices.append(i)
        
        if len(available_indices) > 0:
            best_idx = available_indices[0]
            for idx in available_indices:
                if procs[idx].burst_time < procs[best_idx].burst_time:
                    best_idx = idx
            
            p = procs[best_idx]
            start_time = current_time
            finish_time = start_time + p.burst_time
            
            results.append({
                'pid': p.pid,
                'arrival': p.arrival_time,
                'burst': p.burst_time,
                'prio': p.priority,
                'wt': start_time - p.arrival_time,
                'tat': finish_time - p.arrival_time
            })
            
            current_time = finish_time
            is_completed[best_idx] = True
            completed += 1
        else:
            current_time += 1
    return results

def run_priority(processes_list):
    procs = []
    for p in processes_list:
        procs.append(Process(p.pid, p.arrival_time, p.burst_time, p.priority))
    
    n = len(procs)
    current_time = 0
    completed = 0
    is_completed = [False] * n
    results = []

    while completed < n:
        available_indices = []
        for i in range(n):
            if procs[i].arrival_time <= current_time and is_completed[i] == False:
                available_indices.append(i)
        
        if len(available_indices) > 0:
            best_idx = available_indices[0]
            for idx in available_indices:
                if procs[idx].priority < procs[best_idx].priority:
                    best_idx = idx
                elif procs[idx].priority == procs[best_idx].priority:
                    if procs[idx].arrival_time < procs[best_idx].arrival_time:
                        best_idx = idx
            
            p = procs[best_idx]
            start_time = current_time
            finish_time = start_time + p.burst_time
            
            results.append({
                'pid': p.pid,
                'arrival': p.arrival_time,
                'burst': p.burst_time,
                'prio': p.priority,
                'wt': start_time - p.arrival_time,
                'tat': finish_time - p.arrival_time
            })
            
            current_time = finish_time
            is_completed[best_idx] = True
            completed += 1
        else:
            current_time += 1
    return results

test_data = [
    Process(pid=1, arrival_time=0, burst_time=10, priority=1),
    Process(pid=2, arrival_time=0, burst_time=2, priority=5)
]

sjf_final = run_sjf(test_data)
priority_final = run_priority(test_data)

sjf_avg = display_table("SJF (Non-Preemptive)", sjf_final)
pri_avg = display_table("Priority Scheduling", priority_final)

print("\n--- Final Conclusion ---")
if sjf_avg[0] < pri_avg[0]:
    print("SJF is better in Average Waiting Time.")
else:
    print("Priority is better in Average Waiting Time.")