import random, numpy as np, pandas as pd

import scipy

from scheduler import schedule_tasks
from datetime import datetime

ALGOS = ["fcfs", "sjf", "srtf", "rr", "ps", "edf"]


import random
from datetime import datetime, timedelta
from models import Task, ArrivalTime, DeadlineTime  # adjust import path if needed

def generate_random_task_list(num_tasks, start_date="2025-09-27"):
    tasks = []
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")

    for i in range(num_tasks):
        # Duration between 1–10 hours (float)
        duration = int(round(random.uniform(1, 10)))


        # Random arrival date (within 3 days of start)
        arrival_date_offset = random.randint(0, 2)
        arrival_dt = start_dt + timedelta(days=arrival_date_offset)

        # Random arrival time (0–23)
        arrival_hour = random.randint(0, 23)

        # Calculate realistic deadline
        # Extra hours: between ~1.2x and 3x duration
        extra_hours = random.randint(int(duration * 1.2), int(duration * 3))
        extra_days = random.randint(0, 2)

        # Compute deadline hour and date
        total_hours = arrival_hour + extra_hours
        deadline_hour = total_hours % 24
        deadline_date = (arrival_dt + timedelta(days=extra_days + total_hours // 24)).strftime("%Y-%m-%d")

        # Importance
        importance = random.choice(["Low", "Medium", "High"])

        # Build Task model
        task = Task(
            id=i + 1,
            taskName=f"Task {i}",
            duration=duration,
            arrivalTime=ArrivalTime(
                hrs=arrival_hour,
                date=arrival_dt.strftime("%Y-%m-%d")
            ),
            deadlineTime=DeadlineTime(
                hrs=deadline_hour,
                date=deadline_date
            ),
            importance=importance
        )

        tasks.append(task)

    return tasks




import numpy as np
from datetime import datetime

from datetime import datetime
import numpy as np
import scipy.stats

def extract_batch_features(task_list):
    """Extract optimized scheduling features from a list of Task objects."""

    durations = [t.duration for t in task_list]
    arrivals = [t.arrivalTime.hrs for t in task_list]

    # Convert deadlines to relative hours
    deadlines = []
    for t in task_list:
        arrival_dt = datetime.strptime(t.arrivalTime.date, "%Y-%m-%d")
        deadline_dt = datetime.strptime(t.deadlineTime.date, "%Y-%m-%d")
        days_diff = (deadline_dt - arrival_dt).days
        deadline_hours = days_diff * 24 + t.deadlineTime.hrs
        deadlines.append(deadline_hours)

    importance_map = {"Low": 1, "Medium": 2, "High": 3}
    importances = [importance_map[t.importance] for t in task_list]

    # Convert to numpy
    durations_np = np.array(durations)
    deadlines_np = np.array(deadlines)
    arrivals_np = np.array(arrivals)
    importances_np = np.array(importances)

    num_tasks = len(task_list)
    avg_duration = np.mean(durations_np)
    std_duration = np.std(durations_np)

    deadline_gaps = deadlines_np - arrivals_np
    avg_deadline_gap = np.mean(deadline_gaps)

    # Core workload stats
    total_workload = np.sum(durations_np)
    avg_importance = np.mean(importances_np)
    importance_high_frac = np.sum(importances_np == 3) / num_tasks

    # Derived scheduling metrics
    deadline_tightness_ratio = avg_duration / (avg_deadline_gap + 1e-5)
    workload_density = total_workload / (avg_deadline_gap + 1e-5)
    urgency_index = avg_duration / (avg_deadline_gap + 1e-5)
    importance_weighted_workload = np.mean(durations_np * importances_np)
    duration_to_deadline_variability = std_duration / (avg_deadline_gap + 1e-5)

    load_per_task = total_workload / (num_tasks + 1e-5)
    tightness_x_importance = deadline_tightness_ratio * avg_importance
    duration_var_ratio = std_duration / (avg_duration + 1e-5)
    density_x_tasks = workload_density * num_tasks

    # Slack-based features
    slack = deadlines_np - arrivals_np - durations_np
    avg_slack = np.mean(slack)
    min_slack = np.min(slack)
    slack_std = np.std(slack)
    tightest_slack_ratio = np.min(slack) / (avg_duration + 1e-5)

    # Arrival / inter-arrival features
    arrival_std = np.std(arrivals_np)
    arrival_skew = scipy.stats.skew(arrivals_np)
    arrival_spread = np.max(arrivals_np) - np.min(arrivals_np)

    # Duration / deadline distribution descriptors
    duration_skew = scipy.stats.skew(durations_np)
    deadline_gap_skew = scipy.stats.skew(deadline_gaps)
    duration_range_ratio = (np.max(durations_np) - np.min(durations_np)) / (avg_duration + 1e-5)

    # Importance-related interaction
    importance_skew = (np.sum(importances_np == 3)/num_tasks) - (np.sum(importances_np == 1)/num_tasks)

    # Workload-pressure interactions
    workload_x_density = total_workload * workload_density
    density_x_tightness = workload_density * deadline_tightness_ratio

    # Collect final features
    features = {
        "num_tasks": num_tasks,
        "std_duration": std_duration,
        "total_workload": total_workload,
        "workload_density": workload_density,
        # "duration_to_deadline_variability": duration_to_deadline_variability,
        "density_x_tasks": density_x_tasks,
        # "load_per_task": load_per_task,
        # "tightness_x_importance": tightness_x_importance,
        # "duration_var_ratio": duration_var_ratio,
        # "urgency_index": urgency_index,
        # "importance_weighted_workload": importance_weighted_workload,
        # "avg_slack": avg_slack,
        # "min_slack": min_slack,
        # "slack_std": slack_std,
        # "tightest_slack_ratio": tightest_slack_ratio,
        # "arrival_std": arrival_std,
        # "arrival_skew": arrival_skew,
        "arrival_spread": arrival_spread,
        # "duration_skew": duration_skew,
        # "deadline_gap_skew": deadline_gap_skew,
        "duration_range_ratio": duration_range_ratio,
        # "importance_skew": importance_skew,
        "workload_x_density": workload_x_density,
        "density_x_tightness": density_x_tightness
    }

    return features





import numpy as np
from datetime import datetime

def score_schedule(schedule, task_list):
    """
    Compute an adaptive composite schedule score based on:
      - Turnaround time
      - Waiting time
      - Deadline adherence
      - Importance-weighted early completion
    Compatible with Pydantic Task objects and date-aware schedule entries.
    """

    turnaround = []
    waiting = []
    deadlines_met = 0
    imp_weighted = 0
    n = len(task_list)

    importance_map = {"Low": 1, "Medium": 2, "High": 3}

    # --- Normalize times based on total schedule span ---
    all_times = []
    for s in schedule:
        s_date = datetime.strptime(s["date"], "%Y-%m-%d")
        start_abs = s_date.timestamp() / 3600 + s["start"]
        end_abs = s_date.timestamp() / 3600 + s["end"]
        all_times.extend([start_abs, end_abs])

    total_time_span = max(all_times) - min(all_times)
    if total_time_span == 0:
        total_time_span = 1  # avoid divide-by-zero

    # --- Per-task evaluation ---
    for task in task_list:
        tname = task.taskName
        t_imp = importance_map[task.importance]
        duration = task.duration

        # Compute absolute arrival and deadline in hours
        arrival_date = datetime.strptime(task.arrivalTime.date, "%Y-%m-%d")
        deadline_date = datetime.strptime(task.deadlineTime.date, "%Y-%m-%d")
        arrival_abs = arrival_date.timestamp() / 3600 + task.arrivalTime.hrs
        deadline_abs = deadline_date.timestamp() / 3600 + task.deadlineTime.hrs

        # Get all executions for this task
        task_execs = [s for s in schedule if s["task"] == tname]
        if not task_execs:
            # If not scheduled, penalize heavily
            turnaround.append(total_time_span * 2)
            waiting.append(total_time_span * 2)
            continue

        # Convert schedule entries to absolute hours
        exec_start_times = [
            datetime.strptime(s["date"], "%Y-%m-%d").timestamp() / 3600 + s["start"]
            for s in task_execs
        ]
        exec_end_times = [
            datetime.strptime(s["date"], "%Y-%m-%d").timestamp() / 3600 + s["end"]
            for s in task_execs
        ]

        start_abs = min(exec_start_times)
        end_abs = max(exec_end_times)

        # Compute turnaround & waiting time
        tat = end_abs - arrival_abs
        wt = tat - duration
        turnaround.append(max(tat, 0))
        waiting.append(max(wt, 0))

        # Check deadline compliance
        if end_abs <= deadline_abs:
            deadlines_met += 1

        # Importance-weighted reward (earlier completion → higher)
        imp_weighted += t_imp / (end_abs - min(all_times) + 1e-5)

    # --- Adaptive normalization ---
    mean_turnaround = np.mean(turnaround) / total_time_span
    mean_waiting = np.mean(waiting) / total_time_span
    deadline_score = deadlines_met / n
    importance_score = imp_weighted / n

    # --- Weighted composite score ---
    score = (
        0.25 * (1 - mean_turnaround) +
        0.25 * (1 - mean_waiting) +
        0.30 * deadline_score +
        0.20 * importance_score
    )

    # Ensure the score stays within [0, 1]
    return max(0.0, min(1.0, score))




def generate_dataset_algo(n_batches=1000):
    data = []
    for _ in range(n_batches):
        num_tasks = random.randint(4, 10)
        tasks = generate_random_task_list(num_tasks)
        features = extract_batch_features(tasks)
        best_algo, best_score = None, -float("inf")
        for algo in ALGOS:
            if algo == "rr":
                for tq in [1, 2, 4, 6]:
                    schedule = schedule_tasks(tasks, algo, time_quantum=tq)
                    sc = score_schedule(schedule, tasks)
                    if sc > best_score:
                        best_score, best_algo = sc, algo
                        # features["best_tq"] = tq
            else:
                schedule = schedule_tasks(tasks, algo)
                sc = score_schedule(schedule, tasks)
                if sc > best_score:
                    best_score, best_algo = sc, algo
        idx = ALGOS.index(best_algo)
        features["best_algo"] = idx
        data.append(features)

    return pd.DataFrame(data)

def generate_dataset_tq(n_batches=1000):
    tq_values = [1, 2, 4, 6]
    tq_to_encoded = {tq: i for i, tq in enumerate(tq_values)}  # map to 0–3

    data = []
    for _ in range(n_batches):
        num_tasks = random.randint(4, 10)
        tasks = generate_random_task_list(num_tasks)
        features = extract_batch_features(tasks)

        best_score = -float("inf")
        best_tq = None
        algo = "rr"

        # Find best time quantum
        for tq in tq_values:
            schedule = schedule_tasks(tasks, algo, time_quantum=tq)
            sc = score_schedule(schedule, tasks)
            if sc > best_score:
                best_score, best_tq = sc, tq

        # Store encoded label
        features["best_tq"] = tq_to_encoded[best_tq]
        data.append(features)

    return pd.DataFrame(data)



# # get algo dataset
# df_algo = generate_dataset_algo(20000)
# df_algo.to_csv("synthetic_scheduler_dataset_algo.csv", index=False)
#
#
#
# # get tq dataset
# df_tq = generate_dataset_tq(10000)
# df_tq.to_csv("synthetic_scheduler_dataset_tq.csv", index=False)
