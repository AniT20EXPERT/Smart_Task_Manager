from synthetic_dataset_gen import generate_random_task_list, extract_batch_features,score_schedule
from scheduler import schedule_tasks
tasks = generate_random_task_list(10)
print(tasks)
algo = "sjf"
tq=0
schedule = schedule_tasks(tasks, algo, time_quantum=tq)
print(schedule)

features = extract_batch_features(tasks)
print(features)

sc = score_schedule(schedule, tasks)

print(sc)