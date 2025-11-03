from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scheduler import schedule_tasks
from ai_agent_claude import run_agentic_ai
from synthetic_dataset_gen import extract_batch_features
import pandas as pd
# from ai_agent import run_agentic_ai
import json
from xgboost import XGBClassifier, XGBRegressor
from models import TaskRequest, SuggestionRequest, SchedulerRequest, RlFeedback, Chat_req
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <-- your Vite dev server
    allow_credentials=True,
    allow_methods=["*"],  # allow GET, POST, etc.
    allow_headers=["*"],  # allow all headers
)



@app.get("/")
def root():
    return {"message": "Hello from FastAPI backend!"}





@app.post("/api/validateTask")
def validate_task(request: TaskRequest):
    # i/o----> nlp entry,warnings, suggestions, task summary, suggestion response by user
    # o/p----> warningMsg, suggestionMsg, tasksSummaryMsg: demotaskssummary
    nl_entry = request.nlTask
    user_suggestion_response = request.nlResponse
    warnings = request.warningMsg
    suggestions = request.suggestionMsg
    task_summary = str(request.tasksSummaryMsg)
    print(type(request.tasksSummaryMsg))
    print(task_summary)
    updated_summary, warning_msg, suggestion_msg = run_agentic_ai(
        nl_entry,
        warnings,
        suggestions,
        user_suggestion_response,
        task_summary
    )
    task_summary = updated_summary
    return {
            "warningMsg": warning_msg,
            "suggestionMsg": suggestion_msg,
            "tasksSummaryMsg": json.loads(task_summary)
        }


@app.post("/api/ai_suggest")
def get_ai_suggestion(request: SuggestionRequest):
    task_list = request.task_list
    print(task_list)
    # print(type(task_list))
    algo = "RR"
    tq = 6
    model = XGBClassifier()
    model.load_model("xgb_model_algo.json")
    features = extract_batch_features(task_list)
    suggested_algo = model.predict(pd.DataFrame([features]))[0]
    ALGOS = ["fcfs", "sjf", "srtf", "rr", "ps", "edf"]
    algo = ALGOS[suggested_algo]
    tq_regressor = XGBClassifier()
    tq_regressor.load_model("xgb_model_tq.json")
    if algo == "rr":
        tq_pred = tq_regressor.predict(features)
        tqs = [1,2,4,6]
        tq_pred = tqs[tq_pred]
    else:
        tq_pred = 0  # not applicable

    return {"algo": algo,
            "tq": tq_pred
            }


@app.post("/api/run_scheduler")
def running_scheduler(request: SchedulerRequest):
    task_list = request.task_list
    algo = request.algo
    tq = request.tq
    print(task_list)
    print(algo)
    print(tq)

    schedule = schedule_tasks(task_list, algo, time_quantum=tq)
    print(schedule)
    return schedule

@app.post("/api/rl_feedback")
def getting_feedback(request: RlFeedback):
    choice = request.choice     # manual  |  AI
    print(choice)
    return {"success": True}


@app.post("/api/chat")
def chat_with_bot(request: Chat_req):
    user_msg = request.user_prompt
    task_list = request.task_list
    print(user_msg)
    print(task_list)
    res = "hi there my good friend"
    return {"chat_response": res}