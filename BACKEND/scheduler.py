from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ArrivalTime:
    hrs: int
    date: str


@dataclass
class DeadlineTime:
    hrs: int
    date: str


@dataclass
class Task:
    id: int
    taskName: str
    duration: int
    arrivalTime: ArrivalTime
    deadlineTime: DeadlineTime
    importance: str


def schedule_tasks(task_list: List[Task], algo: str, time_quantum: int = 1) -> List[Dict[str, Any]]:
    """
    Schedule tasks using various scheduling algorithms.

    Args:
        task_list: List of Task objects
        algo: Algorithm name ('fcfs', 'sjf', 'srtf', 'rr', 'priority', 'edf')
        time_quantum: Time quantum for Round Robin (default: 1)

    Returns:
        List of dictionaries with task schedule including dates
    """
    algo = algo.lower().strip()

    if algo == 'fcfs':
        return fcfs_schedule(task_list)
    elif algo == 'sjf':
        return sjf_schedule(task_list)
    elif algo == 'srtf':
        return srtf_schedule(task_list)
    elif algo == 'rr':
        return rr_schedule(task_list, time_quantum)
    elif algo == 'ps':
        return priority_schedule(task_list)
    elif algo == 'edf':
        return edf_schedule(task_list)
    else:
        raise ValueError(f"Unknown algorithm: {algo}")


def get_arrival_timestamp(task: Task) -> datetime:
    """Convert arrival time to datetime timestamp."""
    return datetime.strptime(f"{task.arrivalTime.date} {task.arrivalTime.hrs:02d}:00", "%Y-%m-%d %H:%M")


def get_deadline_timestamp(task: Task) -> datetime:
    """Convert deadline time to datetime timestamp."""
    return datetime.strptime(f"{task.deadlineTime.date} {task.deadlineTime.hrs:02d}:00", "%Y-%m-%d %H:%M")


def get_priority_value(importance: str) -> int:
    """Convert importance string to priority value (lower is higher priority)."""
    importance_map = {
        'high': 1,
        'medium': 2,
        'low': 3
    }
    return importance_map.get(importance.lower().strip(), 2)


def create_schedule_entries(start_dt: datetime, duration: int, task_name: str) -> List[Dict[str, Any]]:
    """Create schedule entries for a task, handling multi-day spans."""
    entries = []
    end_dt = start_dt + timedelta(hours=duration)
    current = start_dt

    while current < end_dt:
        # Calculate end of current day
        day_end = current.replace(hour=23, minute=59, second=59)
        next_day_start = (current + timedelta(days=1)).replace(hour=0, minute=0, second=0)

        # Determine segment end (either end of task or end of day)
        if end_dt <= next_day_start:
            # Task ends today
            segment_end = end_dt
        else:
            # Task continues to next day
            segment_end = next_day_start

        # Calculate hours
        start_hour = current.hour
        if segment_end.date() == current.date():
            end_hour = segment_end.hour
        else:
            end_hour = 24

        entries.append({
            "task": task_name,
            "start": start_hour,
            "end": end_hour,
            "date": current.strftime("%Y-%m-%d")
        })

        # Move to next day
        current = next_day_start

    return entries


def fcfs_schedule(task_list: List[Task]) -> List[Dict[str, Any]]:
    """First Come First Served scheduling."""
    if not task_list:
        return []

    # Sort by arrival time
    sorted_tasks = sorted(task_list, key=lambda t: get_arrival_timestamp(t))

    schedule = []
    current_time = get_arrival_timestamp(sorted_tasks[0])

    for task in sorted_tasks:
        task_arrival = get_arrival_timestamp(task)

        # Wait for task to arrive if necessary
        if task_arrival > current_time:
            current_time = task_arrival

        # Schedule the task
        entries = create_schedule_entries(current_time, task.duration, task.taskName)
        schedule.extend(entries)

        # Update current time
        current_time = current_time + timedelta(hours=task.duration)

    return schedule


def sjf_schedule(task_list: List[Task]) -> List[Dict[str, Any]]:
    """Shortest Job First (non-preemptive) scheduling."""
    if not task_list:
        return []

    schedule = []
    remaining = task_list.copy()
    current_time = get_arrival_timestamp(min(task_list, key=lambda t: get_arrival_timestamp(t)))

    while remaining:
        # Find all tasks that have arrived by current_time
        available = [t for t in remaining if get_arrival_timestamp(t) <= current_time]

        if not available:
            # Jump to the next task arrival
            next_task = min(remaining, key=lambda t: get_arrival_timestamp(t))
            current_time = get_arrival_timestamp(next_task)
            continue

        # Select the shortest job
        selected = min(available, key=lambda t: t.duration)

        # Schedule it
        entries = create_schedule_entries(current_time, selected.duration, selected.taskName)
        schedule.extend(entries)

        # Update time and remove task
        current_time = current_time + timedelta(hours=selected.duration)
        remaining.remove(selected)

    return schedule


def srtf_schedule(task_list: List[Task]) -> List[Dict[str, Any]]:
    """Shortest Remaining Time First (preemptive SJF) scheduling."""
    if not task_list:
        return []

    # Track remaining time for each task
    remaining_time = {task.id: task.duration for task in task_list}
    completed = set()

    schedule = []
    current_time = get_arrival_timestamp(min(task_list, key=lambda t: get_arrival_timestamp(t)))

    while len(completed) < len(task_list):
        # Find all available tasks
        available = [
            t for t in task_list
            if t.id not in completed and get_arrival_timestamp(t) <= current_time
        ]

        if not available:
            # Jump to next arrival
            unarrived = [t for t in task_list if t.id not in completed]
            if unarrived:
                next_task = min(unarrived, key=lambda t: get_arrival_timestamp(t))
                current_time = get_arrival_timestamp(next_task)
            continue

        # Select task with shortest remaining time
        selected = min(available, key=lambda t: remaining_time[t.id])

        # Execute for 1 hour
        entries = create_schedule_entries(current_time, 1, selected.taskName)
        schedule.extend(entries)

        remaining_time[selected.id] -= 1
        current_time = current_time + timedelta(hours=1)

        if remaining_time[selected.id] == 0:
            completed.add(selected.id)

    # Merge consecutive entries of same task on same date
    return merge_consecutive(schedule)


def rr_schedule(task_list: List[Task], time_quantum: int) -> List[Dict[str, Any]]:
    """Round Robin scheduling."""
    if not task_list:
        return []

    # Sort by arrival
    sorted_tasks = sorted(task_list, key=lambda t: get_arrival_timestamp(t))

    # Track remaining time
    remaining_time = {task.id: task.duration for task in task_list}

    schedule = []
    current_time = get_arrival_timestamp(sorted_tasks[0])
    ready_queue = []
    next_arrival_idx = 0

    # Add first arrived task
    while next_arrival_idx < len(sorted_tasks) and get_arrival_timestamp(
            sorted_tasks[next_arrival_idx]) <= current_time:
        ready_queue.append(sorted_tasks[next_arrival_idx])
        next_arrival_idx += 1

    while ready_queue or next_arrival_idx < len(sorted_tasks):
        if not ready_queue:
            # Jump to next arrival
            current_time = get_arrival_timestamp(sorted_tasks[next_arrival_idx])
            while next_arrival_idx < len(sorted_tasks) and get_arrival_timestamp(
                    sorted_tasks[next_arrival_idx]) <= current_time:
                ready_queue.append(sorted_tasks[next_arrival_idx])
                next_arrival_idx += 1
            continue

        # Get next task from queue
        current_task = ready_queue.pop(0)

        # Execute for time quantum or remaining time
        exec_time = min(time_quantum, remaining_time[current_task.id])

        entries = create_schedule_entries(current_time, exec_time, current_task.taskName)
        schedule.extend(entries)

        remaining_time[current_task.id] -= exec_time
        current_time = current_time + timedelta(hours=exec_time)

        # Add newly arrived tasks
        while next_arrival_idx < len(sorted_tasks) and get_arrival_timestamp(
                sorted_tasks[next_arrival_idx]) <= current_time:
            ready_queue.append(sorted_tasks[next_arrival_idx])
            next_arrival_idx += 1

        # Re-add current task if not finished
        if remaining_time[current_task.id] > 0:
            ready_queue.append(current_task)

    return schedule


def priority_schedule(task_list: List[Task]) -> List[Dict[str, Any]]:
    """Priority scheduling based on importance (High > Medium > Low)."""
    if not task_list:
        return []

    schedule = []
    remaining = task_list.copy()
    current_time = get_arrival_timestamp(min(task_list, key=lambda t: get_arrival_timestamp(t)))

    while remaining:
        # Find available tasks
        available = [t for t in remaining if get_arrival_timestamp(t) <= current_time]

        if not available:
            # Jump to next arrival
            next_task = min(remaining, key=lambda t: get_arrival_timestamp(t))
            current_time = get_arrival_timestamp(next_task)
            continue

        # Select highest priority (lowest priority value)
        selected = min(available, key=lambda t: get_priority_value(t.importance))

        # Schedule it
        entries = create_schedule_entries(current_time, selected.duration, selected.taskName)
        schedule.extend(entries)

        # Update time
        current_time = current_time + timedelta(hours=selected.duration)
        remaining.remove(selected)

    return schedule


def edf_schedule(task_list: List[Task]) -> List[Dict[str, Any]]:
    """Earliest Deadline First scheduling."""
    if not task_list:
        return []

    schedule = []
    remaining = list(task_list)  # Create a fresh copy
    current_time = get_arrival_timestamp(min(task_list, key=lambda t: get_arrival_timestamp(t)))

    while remaining:
        # Find tasks that have arrived
        available = [t for t in remaining if get_arrival_timestamp(t) <= current_time]

        if not available:
            # No tasks available, jump to next arrival
            next_task = min(remaining, key=lambda t: get_arrival_timestamp(t))
            current_time = get_arrival_timestamp(next_task)
            # Don't use continue here, let it check available again
            available = [t for t in remaining if get_arrival_timestamp(t) <= current_time]

        if available:
            # Select task with earliest deadline
            selected = min(available, key=lambda t: get_deadline_timestamp(t))

            # Schedule the task
            entries = create_schedule_entries(current_time, selected.duration, selected.taskName)
            schedule.extend(entries)

            # Update time and remove from remaining
            current_time = current_time + timedelta(hours=selected.duration)
            remaining.remove(selected)

    return schedule


def merge_consecutive(schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge consecutive entries of the same task on the same date."""
    if not schedule:
        return []

    merged = []
    current = schedule[0].copy()

    for entry in schedule[1:]:
        # Check if same task, same date, and consecutive times
        if (entry['task'] == current['task'] and
                entry['date'] == current['date'] and
                entry['start'] == current['end']):
            # Merge by extending end time
            current['end'] = entry['end']
        else:
            # Save current and start new one
            merged.append(current)
            current = entry.copy()

    merged.append(current)
    return merged


