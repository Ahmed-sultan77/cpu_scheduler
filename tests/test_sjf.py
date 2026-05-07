def run_sjf(processes_list):
    procs = []
    for p in processes_list:
        procs.append({
            'pid': p.pid,
            'arrival': p.arrival_time,
            'burst': p.burst_time,
            'prio': p.priority
        })
    
    n = len(procs)
    current_time = 0
    completed = 0
    is_completed = [False] * n
    results = []

    while completed < n:
        available_indices = []
        for i in range(n):
            if procs[i]['arrival'] <= current_time and is_completed[i] == False:
                available_indices.append(i)
        
        if len(available_indices) > 0:
            best_idx = available_indices[0]
            for idx in available_indices:
                if procs[idx]['burst'] < procs[best_idx]['burst']:
                    best_idx = idx
            
            p = procs[best_idx]
            
            start_time = current_time
            finish_time = start_time + p['burst']
            
            results.append({
                'pid': p['pid'],
                'arrival': p['arrival'],
                'burst': p['burst'],
                'start': start_time,
                'finish': finish_time,
                'wt': start_time - p['arrival'],
                'tat': finish_time - p['arrival'],
                'rt': start_time - p['arrival']
            })
            
            current_time = finish_time
            is_completed[best_idx] = True
            completed = completed + 1
        else:
            current_time = current_time + 1
            
    return results