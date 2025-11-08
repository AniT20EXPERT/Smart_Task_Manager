import json
import requests
import os
from typing import List
from models import Chat_req, TaskItem
from dotenv import load_dotenv
load_dotenv()
# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "qwen/qwen3-32b"


def call_groq_chat(prompt: str, model: str = GROQ_MODEL, temperature: float = 0.1, max_tokens: int = 2000) -> str:
    """Call Groq API with chat completion format."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY environment variable not set")

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=90
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            error_msg = f"Groq API error: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f" - {error_detail}"
            except:
                error_msg += f" - {response.text}"
            raise Exception(error_msg)

    except requests.exceptions.Timeout:
        raise Exception("Groq API request timed out")
    except Exception as e:
        raise Exception(f"Error calling Groq API: {str(e)}")


def update_tasklist_with_llm(user_message: str, schedule_list: List[TaskItem]):
    """
    Sends user instructions and current schedule list to the LLM,
    updates the schedule according to the instruction,
    and returns the model's response + updated list.
    """
    # ✅ Convert Pydantic models to plain dicts
    schedule_dicts = [task.dict() for task in schedule_list]

    # Build prompt for the model
    prompt = f"""
    You are a precise scheduling assistant that manages a multi-day task schedule.

    **INPUT:**
    1. User's natural language request
    2. Complete schedule in JSON format (each task has: task, start, end, date)

    **CORE PRINCIPLES:**
    - Modify ONLY what the user explicitly requests
    - Preserve ALL tasks from unaffected dates unchanged
    - Maintain task durations unless explicitly asked to change them
    - Return the COMPLETE schedule (all dates) even if only one date was modified

    ---

    **HANDLING DIFFERENT REQUEST TYPES:**

    **1. DELETIONS** ("remove Task A", "delete morning tasks")
       → Remove matching tasks, keep remaining tasks at their original times UNLESS user says "rearrange" or "shift"

    **2. REARRANGING/SHIFTING** ("rearrange", "shift forward", "fill gaps")
       → After any deletions, move remaining tasks on THAT DATE ONLY to fill time gaps
       → Keep task durations intact, maintain chronological order
       → Start from earliest available time slot

    **3. ADDITIONS** ("add Task E from 14-16")
       → Insert new task at specified time
       → Do NOT automatically move other tasks unless they overlap or user requests rearrangement

    **4. TIME CHANGES** ("move Task A to 10am", "reschedule Task B to tomorrow")
       → Update only the specified task's time/date
       → Handle date changes only when explicitly mentioned (e.g., "tomorrow", "next Monday")

    **5. QUERIES** ("how many tasks?", "what's scheduled?")
       → Provide answer in agent_response
       → Return tasklist unchanged

    **6. AMBIGUOUS REQUESTS**
       → If unclear which date is meant, apply to the earliest relevant date
       → If "today" or "tomorrow" is mentioned, calculate based on current date context
       → State your interpretation in agent_response

    ---

    **CRITICAL RULES:**
    ✓ Always output valid JSON with exactly two keys: "agent_response" and "tasklist"
    ✓ "tasklist" must contain ALL tasks from ALL dates, even unmodified ones
    ✓ Times use 24-hour format (0-23 for hours)
    ✓ Dates use YYYY-MM-DD format
    ✓ When rearranging, tasks should start at the earliest available time on that date
    ✓ Never change dates unless explicitly requested
    ✓ Preserve original task order when no rearrangement is requested

    ---

    **EXAMPLES:**

    Example 1 - Remove with rearrangement:
    User: "Remove Task A and rearrange"
    → Delete all Task A entries from specified date, shift remaining tasks to fill gaps

    Example 2 - Remove without rearrangement:
    User: "Delete Task B"
    → Remove Task B entries but keep all other tasks at their original times

    Example 3 - Query:
    User: "How many tasks on 2025-10-10?"
    → Count and respond, return full schedule unchanged

    Example 4 - Scoped change:
    User: "On October 10th, remove Task C"
    → Only modify 2025-10-10, leave 2025-10-11 completely untouched

    ---

    **USER REQUEST:**
    {user_message}

    **CURRENT SCHEDULE:**
    {json.dumps(schedule_dicts, indent=2)}

    **OUTPUT REQUIREMENT:**
    Return ONLY valid JSON:
    {{
      "agent_response": "Brief natural language explanation of changes made",
      "tasklist": [/* complete updated schedule with all dates */]
    }}
    """

    print(prompt)

    # Call Groq API instead of Ollama
    model_output = call_groq_chat(prompt)

    # Try to parse JSON
    try:
        result = json.loads(model_output)
        print(result)
    except json.JSONDecodeError:
        # In case model outputs extra text around JSON
        json_start = model_output.find("{")
        json_end = model_output.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            json_str = model_output[json_start:json_end]
            result = json.loads(json_str)
        else:
            # If JSON parsing completely fails, return error
            result = {
                "agent_response": "Error: Could not parse model response as JSON",
                "tasklist": schedule_dicts  # Return original schedule
            }

    return result


def llm_call(user_msg, task_list):
    result = update_tasklist_with_llm(user_msg, task_list)
    schedule_list = result['tasklist']
    res = result['agent_response']

    # schedule_list = [
    #                  {"task":"Task B","start":10,"end":12,"date":"2025-10-10"},
    #                  {"task":"Task C","start":14,"end":16,"date":"2025-10-10"},
    #                  {"task":"Task B","start":16,"end":18,"date":"2025-10-10"},
    #                  {"task":"Task D","start":18,"end":20,"date":"2025-10-10"},
    #                  {"task":"Task C","start":22,"end":24,"date":"2025-10-10"},
    #                  {"task":"Task B","start":0,"end":2,"date":"2025-10-11"},
    #                  {"task":"Task D","start":2,"end":4,"date":"2025-10-11"},
    #                  {"task":"Task C","start":5,"end":6,"date":"2025-10-11"},
    #                  {"task":"Task D","start":6,"end":7,"date":"2025-10-11"}
    #                 ]

    return schedule_list, res