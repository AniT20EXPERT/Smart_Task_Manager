from pydantic import BaseModel
from typing import List
class TaskRequest(BaseModel):
    nlTask: str
    nlResponse: str
    warningMsg: str
    suggestionMsg: str
    tasksSummaryMsg: List


class ArrivalTime(BaseModel):
    hrs: int
    date: str  # you can later convert this to datetime.date if needed

class DeadlineTime(BaseModel):
    hrs: int
    date: str  # you can later convert this to datetime.date if needed

class Task(BaseModel):
    id: int
    taskName: str
    duration: int
    arrivalTime: ArrivalTime
    deadlineTime: DeadlineTime
    importance: str

class SuggestionRequest(BaseModel):
    task_list: List[Task]


class SchedulerRequest(BaseModel):
    task_list: List[Task]
    algo: str
    tq: int


class RlFeedback(BaseModel):
    choice: str

class Chat_req(BaseModel):
    task_list: str
    user_prompt: str