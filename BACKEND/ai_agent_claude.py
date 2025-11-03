import requests
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional


def run_agentic_ai(
        nl_entry: str,
        warnings: str,
        suggestions: str,
        user_suggestion_response: str,
        task_summary: str
) -> Tuple[str, str, str]:
    """
    Process natural language task entry through Negotiator and Planner agents.

    Args:
        nl_entry: Natural language task input from user
        warnings: Previous warnings from Negotiator
        suggestions: Previous suggestions from Planner
        user_suggestion_response: User's response to suggestions
        task_summary: Current task summary as JSON string

    Returns:
        Tuple of (updated_task_summary_string, warning_msg, suggestion_msg)
    """

    # Parse task_summary from string to list
    try:
        task_list = json.loads(task_summary) if task_summary and task_summary.strip() else []
        print(f"Parsed existing task_list: {len(task_list)} tasks")
    except Exception as e:
        print(f"Error parsing task_summary: {e}")
        task_list = []

    # Initialize return values
    updated_task_summary = task_list.copy()
    print(f"Initial updated_task_summary: {len(updated_task_summary)} tasks")
    warning_msg = ""
    suggestion_msg = ""
    extracted_tasks = []  # Store extracted tasks from new entry

    # Track the number of existing tasks before adding new ones
    num_existing_tasks = len(updated_task_summary)

    # Step 1: Process new task entry FIRST (if provided)
    if nl_entry and nl_entry.strip():
        print(f"Processing new task entry: {nl_entry[:50]}...")

        # Extract basic task info from NL entry using LLM
        extracted_tasks = extract_task_info_with_llm(nl_entry)
        print(f"Extracted {len(extracted_tasks)} tasks")
        print(f"Extracted tasks: {json.dumps(extracted_tasks, indent=2)}")

        # Run Negotiator to check for missing info
        warning_msg = run_negotiator(extracted_tasks, nl_entry)
        print(f"Warning message: {warning_msg[:100]}")

        # Check if there are actual warnings (not the success message)
        has_warnings = "⚠️" in warning_msg

        # Always add extracted tasks to summary
        print(f"Before extend: {len(updated_task_summary)} tasks")
        updated_task_summary.extend(extracted_tasks)
        print(f"After extend: {len(updated_task_summary)} tasks")

        # If no warnings, run Planner to generate detailed suggestions
        if not has_warnings:
            suggestion_msg = run_planner(extracted_tasks, nl_entry, updated_task_summary)
        else:
            # If there are warnings, still show basic confirmation
            suggestion_msg = "⏳ Please provide missing information before I can suggest optimizations."

    # Step 2: Handle user response to previous suggestions (if provided)
    if user_suggestion_response and user_suggestion_response.strip() and suggestions:
        # Handle user response to planner's suggestion with intelligent modification
        # Pass the number of existing tasks to protect them
        response_msg, updated_task_summary = handle_user_response_with_reasoning(
            user_suggestion_response,
            suggestions,
            updated_task_summary,
            num_existing_tasks  # NEW: Pass count of tasks to protect
        )

        # If accepted, keep existing warnings or use new ones
        if "accepted" in response_msg.lower() or "modified" in response_msg.lower():
            # If we just processed new tasks, use those warnings, otherwise use existing
            if not warning_msg:
                warning_msg = warnings if warnings else "✅ No warnings. All information complete."
            # Use the response message as suggestion
            suggestion_msg = response_msg
            task_summary_string = json.dumps(updated_task_summary, indent=4)
            return task_summary_string, warning_msg, suggestion_msg

        # If rejected, acknowledge
        if "rejected" in response_msg.lower():
            # If we just processed new tasks, use those warnings
            if not warning_msg:
                warning_msg = warnings if warnings else "⏳ Awaiting task entry."
            suggestion_msg = "👌 Understood. Feel free to provide new task details or modifications."
            task_summary_string = json.dumps(updated_task_summary, indent=4)
            return task_summary_string, warning_msg, suggestion_msg

    # Step 3: Handle case where nothing was provided
    if not nl_entry.strip() and (not user_suggestion_response or not user_suggestion_response.strip()):
        warning_msg = warnings if warnings else "⏳ Awaiting task entry."
        suggestion_msg = suggestions if suggestions else "⏳ Awaiting task entry."

    # Convert task list back to JSON string
    task_summary_string = json.dumps(updated_task_summary, indent=4)

    return task_summary_string, warning_msg, suggestion_msg


def handle_user_response_with_reasoning(
        user_response: str,
        previous_suggestion: str,
        task_summary: List[Dict],
        num_existing_tasks: int = 0  # NEW: Number of tasks to protect from modification
) -> Tuple[str, List[Dict]]:
    """
    Handle user's response to suggestions with intelligent task modification using LLM.
    """
    user_lower = user_response.lower().strip()

    # Check if user is rejecting
    if any(word in user_lower for word in ["reject", "no", "decline", "disagree", "don't", "not now"]):
        return "❌ Suggestion rejected. Please provide more details.", task_summary

    # Check if user is accepting or providing modification instructions
    is_acceptance = any(word in user_lower for word in
                        ["accept", "yes", "ok", "agree", "sounds good", "perfect", "sure", "please", "pls"])

    # If simple acceptance without modification instructions
    if is_acceptance and len(user_response.split()) <= 3:
        return "✅ Great! Your suggestion has been accepted. The tasks are ready to be scheduled.", task_summary

    # If user provides modification instructions, use LLM to intelligently modify tasks
    if is_acceptance or "break" in user_lower or "split" in user_lower or "divide" in user_lower or "modify" in user_lower:
        print(f"User wants to modify tasks based on: {user_response}")

        # Use LLM to understand and apply modifications
        # NEW: Pass num_existing_tasks to protect old tasks
        modified_tasks = apply_modifications_with_llm(
            user_response,
            previous_suggestion,
            task_summary,
            num_existing_tasks
        )

        if modified_tasks and len(modified_tasks) != len(task_summary):
            return "✅ Tasks modified as requested! I've updated your task list based on your instructions.", modified_tasks
        elif modified_tasks:
            return "✅ Tasks updated! The modifications have been applied.", modified_tasks
        else:
            return "✅ Suggestion accepted! Tasks are ready to be scheduled.", task_summary

    # Default case
    return f"💡 Updated Suggestion: I understand you want to modify. {user_response[:100]}", task_summary


def apply_modifications_with_llm(
        user_instruction: str,
        original_suggestion: str,
        current_tasks: List[Dict],
        num_existing_tasks: int = 0  # NEW: Number of existing tasks to protect
) -> List[Dict]:
    """
    Use LLM reasoning to intelligently modify tasks based on user instructions.
    Only modifies newly added tasks, preserves all existing tasks.
    """

    current_date = datetime.now().strftime("%Y-%m-%d")

    # NEW: Separate existing tasks (to be preserved) from new tasks (can be modified)
    existing_tasks = current_tasks[:num_existing_tasks]
    new_tasks = current_tasks[num_existing_tasks:]

    print(f"Protecting {len(existing_tasks)} existing tasks, modifying {len(new_tasks)} new tasks")

    prompt = f"""You are a task modification expert. The user wants to modify their task list based on their instructions.

IMPORTANT: Only modify the NEW TASKS below. Do NOT modify or remove any existing tasks.

NEW TASKS (can be modified):
{json.dumps(new_tasks, indent=2)}

NUMBER OF EXISTING TASKS (must be preserved): {len(existing_tasks)}

PREVIOUS SUGGESTION FROM SYSTEM:
{original_suggestion}

USER'S MODIFICATION INSTRUCTION:
"{user_instruction}"

YOUR TASK:
Analyze the user's instruction and modify ONLY the new tasks accordingly. Common modifications include:
1. Breaking a task into subtasks (e.g., "break report into draft and review")
2. Adjusting durations (e.g., "make each subtask 2 hours")
3. Changing priorities
4. Adjusting times/dates

CRITICAL RULES:
- ONLY modify the new tasks shown above
- Do NOT remove or modify any existing tasks
- If breaking a task into subtasks, REMOVE the original task from new tasks and ADD the new subtasks
- Preserve all original task attributes (dates, times, importance) unless user specifies changes
- When splitting duration, ensure subtasks add up to original duration (or use user-specified durations)
- If user says "break X into Y and Z of Nhrs each", create Y and Z tasks with Duration=N
- Keep same arrivaldate/deadlinedate for subtasks unless specified otherwise
- For subtasks, use null for arrivaltime if not specified, but preserve deadlinedate/deadlinetime
- If original task had "write report", subtasks should be "draft report", "review report", etc.

OUTPUT FORMAT:
Return ONLY a valid JSON array of the MODIFIED NEW TASKS, nothing else:

[
  {{
    "TaskName": "task name",
    "Duration": hours_or_null,
    "arrivaltime": hour_0_to_23_or_null,
    "arrivaldate": "YYYY-MM-DD_or_null",
    "deadlinetime": hour_0_to_23_or_null,
    "deadlinedate": "YYYY-MM-DD_or_null",
    "importance": "High_or_Medium_or_Low"
  }}
]

NOW APPLY THE MODIFICATION TO THE NEW TASKS ONLY. Return only the JSON array:"""

    response = call_ollama(prompt)
    print(f"LLM Modification Response:\n{response}\n")

    # Try to parse the response
    try:
        # Strategy 1: Direct JSON parsing
        modified_new_tasks = json.loads(response.strip())
        if isinstance(modified_new_tasks, list) and len(modified_new_tasks) > 0:
            validated_new_tasks = validate_and_clean_tasks(modified_new_tasks)
            # NEW: Combine existing tasks + modified new tasks
            return existing_tasks + validated_new_tasks
    except:
        pass

    # Strategy 2: Find JSON array in response
    try:
        cleaned = response.strip()
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)

        json_match = re.search(r'\[\s*\{.*?\}\s*(?:,\s*\{.*?\}\s*)*\]', cleaned, re.DOTALL)
        if json_match:
            modified_new_tasks = json.loads(json_match.group())
            if isinstance(modified_new_tasks, list) and len(modified_new_tasks) > 0:
                validated_new_tasks = validate_and_clean_tasks(modified_new_tasks)
                # NEW: Combine existing tasks + modified new tasks
                return existing_tasks + validated_new_tasks
    except Exception as e:
        print(f"Modification parsing failed: {e}")

    # Fallback: Try simple rule-based modification
    print("LLM modification failed, attempting rule-based fallback")
    modified_new_tasks = rule_based_task_modification(user_instruction, new_tasks)
    # NEW: Combine existing tasks + modified new tasks
    return existing_tasks + modified_new_tasks


def rule_based_task_modification(user_instruction: str, tasks: List[Dict]) -> List[Dict]:
    """
    Fallback: Simple rule-based task modification when LLM fails.
    Only modifies the tasks passed to it (new tasks).
    """
    user_lower = user_instruction.lower()

    # Check if user wants to break a task
    if "break" in user_lower or "split" in user_lower or "divide" in user_lower:
        # Try to find which task to break
        for task in tasks:
            task_name_lower = task.get("TaskName", "").lower()

            # Check if this task is mentioned in the instruction
            if any(word in user_lower for word in task_name_lower.split()):
                # Found the task to break
                original_duration = task.get("Duration", 4)

                # Try to extract number of hours for each subtask
                hours_match = re.search(r'(\d+)\s*hrs?\s+each', user_lower)
                if hours_match:
                    subtask_duration = int(hours_match.group(1))
                else:
                    # Split duration evenly (assume 2 subtasks)
                    subtask_duration = original_duration // 2

                # Extract subtask names from instruction
                # Look for patterns like "into X and Y"
                subtask_match = re.search(r'into\s+([\w\s]+)\s+and\s+([\w\s]+)', user_instruction, re.IGNORECASE)

                if subtask_match:
                    subtask1_name = subtask_match.group(1).strip()
                    subtask2_name = subtask_match.group(2).strip()
                    # Remove "of Xhrs" from names
                    subtask1_name = re.sub(r'\s+of\s+\d+hrs?', '', subtask1_name)
                    subtask2_name = re.sub(r'\s+of\s+\d+hrs?', '', subtask2_name)
                else:
                    # Default names
                    base_name = task.get("TaskName", "task")
                    subtask1_name = f"draft {base_name}"
                    subtask2_name = f"review {base_name}"

                # Create subtasks
                subtask1 = task.copy()
                subtask1["TaskName"] = subtask1_name
                subtask1["Duration"] = subtask_duration
                subtask1["arrivaltime"] = None  # Flexible start

                subtask2 = task.copy()
                subtask2["TaskName"] = subtask2_name
                subtask2["Duration"] = subtask_duration
                subtask2["arrivaltime"] = None  # Flexible start

                # Replace original task with subtasks in the new tasks list
                modified_tasks = [t for t in tasks if t.get("TaskName") != task.get("TaskName")]
                modified_tasks.extend([subtask1, subtask2])

                return modified_tasks

    # If no modification could be applied, return original tasks unchanged
    return tasks


def call_ollama(prompt: str, model: str = "mistral:latest") -> str:
    """Call Ollama API with given prompt."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1,
                "num_predict": 1500
            },
            timeout=90
        )

        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            return f"Error calling Ollama: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"


def extract_task_info_with_llm(nl_entry: str) -> List[Dict]:
    """
    Extract structured task information from natural language using LLM reasoning.
    Uses chain-of-thought prompting for better comprehension.
    """

    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M")
    day_of_week = datetime.now().strftime("%A")
    current_year = datetime.now().year

    prompt = f"""You are an expert task extraction system. Extract ALL tasks from the user's natural language input.

CURRENT CONTEXT:
- Date: {current_date} ({day_of_week})
- Time: {current_time}
- Year: {current_year}

USER INPUT:
"{nl_entry}"

STEP 1 - IDENTIFY TASKS:
First, identify how many separate tasks are mentioned. Tasks are usually separated by commas, "and", or semicolons.

STEP 2 - EXTRACT INFORMATION FOR EACH TASK:
For each task, extract:
- Task name (the action to be done)
- Duration (how long it takes - look for "Xhr", "X hours", "Xhrs")
- Start time (when to begin - look for times like "6am", "6:00", "18:00")
- Start date (what day to start - look for dates like "2/10/2025", "tomorrow", "today")
- Deadline time (when it must be completed - look for "by", "before", "complete by")
- Deadline date (deadline day - may reference "same day" as another date)
- Importance (High/Medium/Low based on urgency words)

STEP 3 - REASONING RULES:
- "same day" means use the previously mentioned date
- "anytime" for start time means null (flexible start)
- "before Xam" means deadline time is X in 24h format
- "6am" = 6, "6pm" = 18 in 24-hour format
- Dates like "2/10/2025" - use DAY/MONTH/YEAR format (2 is day, 10 is month)
- Convert to YYYY-MM-DD format (2/10/2025 = 2025-10-02)
- If deadline is on same day as start, use same date
- If time not specified but implied from context, infer it

STEP 4 - OUTPUT FORMAT:
Return ONLY a valid JSON array, nothing else:

[
  {{
    "TaskName": "task description",
    "Duration": hours_as_integer_or_null,
    "arrivaltime": hour_0_to_23_or_null,
    "arrivaldate": "YYYY-MM-DD_or_null",
    "deadlinetime": hour_0_to_23_or_null,
    "deadlinedate": "YYYY-MM-DD_or_null",
    "importance": "High_or_Medium_or_Low"
  }}
]

EXAMPLE INPUT:
"walk dog 2hrs 6am 2/10/2025 complete before 9am same day, write report 4hrs by 2/10/2025 6pm start same day anytime"

EXAMPLE REASONING:
Task 1: "walk dog"
- Duration: 2 hours → 2
- Start: 6am on 2/10/2025 → arrivaltime: 6, arrivaldate: "2025-10-02"
- Deadline: before 9am same day → deadlinetime: 9, deadlinedate: "2025-10-02"

Task 2: "write report"
- Duration: 4 hours → 4
- Start: same day anytime → arrivaltime: null, arrivaldate: "2025-10-02"
- Deadline: by 6pm on 2/10/2025 → deadlinetime: 18, deadlinedate: "2025-10-02"

EXAMPLE OUTPUT:
[
  {{
    "TaskName": "walk dog",
    "Duration": 2,
    "arrivaltime": 6,
    "arrivaldate": "2025-10-02",
    "deadlinetime": 9,
    "deadlinedate": "2025-10-02",
    "importance": "Medium"
  }},
  {{
    "TaskName": "write report",
    "Duration": 4,
    "arrivaltime": null,
    "arrivaldate": "2025-10-02",
    "deadlinetime": 18,
    "deadlinedate": "2025-10-02",
    "importance": "Medium"
  }}
]

NOW EXTRACT FROM THE USER INPUT ABOVE. Return only the JSON array:"""

    response = call_ollama(prompt)

    print(f"LLM Response:\n{response}\n")  # Debug logging

    # Try multiple parsing strategies
    extracted_tasks = None

    # Strategy 1: Direct JSON parsing
    try:
        extracted_tasks = json.loads(response.strip())
        if isinstance(extracted_tasks, list) and len(extracted_tasks) > 0:
            return validate_and_clean_tasks(extracted_tasks)
    except:
        pass

    # Strategy 2: Find JSON array in response
    try:
        # Remove markdown code blocks
        cleaned = response.strip()
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)

        # Find JSON array
        json_match = re.search(r'\[\s*\{.*?\}\s*(?:,\s*\{.*?\}\s*)*\]', cleaned, re.DOTALL)
        if json_match:
            extracted_tasks = json.loads(json_match.group())
            if isinstance(extracted_tasks, list) and len(extracted_tasks) > 0:
                return validate_and_clean_tasks(extracted_tasks)
    except Exception as e:
        print(f"Strategy 2 failed: {e}")

    # Strategy 3: Try to fix common JSON issues
    try:
        # Fix common issues like trailing commas, missing quotes
        cleaned = response.strip()
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)  # Remove trailing commas
        cleaned = re.sub(r'(\w+):', r'"\1":', cleaned)  # Add quotes to keys

        json_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if json_match:
            extracted_tasks = json.loads(json_match.group())
            if isinstance(extracted_tasks, list) and len(extracted_tasks) > 0:
                return validate_and_clean_tasks(extracted_tasks)
    except Exception as e:
        print(f"Strategy 3 failed: {e}")

    # Strategy 4: Use regex-based extraction as absolute fallback
    print("All LLM strategies failed, using regex fallback")
    return regex_based_fallback(nl_entry)


def validate_and_clean_tasks(tasks: List[Dict]) -> List[Dict]:
    """Validate and clean extracted tasks."""
    validated = []

    for task in tasks:
        if not isinstance(task, dict):
            continue

        task_name = task.get("TaskName") or task.get("taskName") or task.get("task_name")
        if not task_name:
            continue

        # Clean and validate each field
        cleaned_task = {
            "TaskName": str(task_name).strip(),
            "Duration": safe_int(task.get("Duration") or task.get("duration")),
            "arrivaltime": safe_int(task.get("arrivaltime") or task.get("arrival_time")),
            "arrivaldate": task.get("arrivaldate") or task.get("arrival_date"),
            "deadlinetime": safe_int(task.get("deadlinetime") or task.get("deadline_time")),
            "deadlinedate": task.get("deadlinedate") or task.get("deadline_date"),
            "importance": task.get("importance") or task.get("Importance") or "Medium"
        }

        # Ensure importance is valid
        if cleaned_task["importance"] not in ["High", "Medium", "Low"]:
            cleaned_task["importance"] = "Medium"

        validated.append(cleaned_task)

    return validated


def safe_int(value) -> Optional[int]:
    """Safely convert value to int or return None."""
    if value is None or value == "null" or value == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def regex_based_fallback(nl_entry: str) -> List[Dict]:
    """
    Enhanced regex-based extraction as absolute fallback.
    """
    tasks = []

    # Split by task separators
    segments = re.split(r',(?![^()]*\))|\band\b|;', nl_entry)

    # Track last seen date for "same day" references
    last_date = None

    for segment in segments:
        original_segment = segment.strip()
        if len(original_segment) < 3:
            continue

        # Make a working copy for extraction
        working_text = original_segment

        task = {
            "TaskName": "",
            "Duration": None,
            "arrivaltime": None,
            "arrivaldate": None,
            "deadlinetime": None,
            "deadlinedate": None,
            "importance": "Medium"
        }

        # Extract duration and remove from working text
        duration_match = re.search(r'(\d+)\s*(?:hrs?|hours?)', working_text, re.IGNORECASE)
        if duration_match:
            task["Duration"] = int(duration_match.group(1))
            working_text = working_text.replace(duration_match.group(0), ' ')

        # Extract dates (D/M/YYYY format) and remove from working text
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', working_text)
        if date_match:
            day, month, year = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
            date_str = f"{year}-{month:02d}-{day:02d}"
            last_date = date_str

            # Check if this is a deadline or arrival
            before_date = working_text[:date_match.start()]
            if re.search(r'\b(by|before|due|deadline|complete|finish)\b', before_date, re.IGNORECASE):
                task["deadlinedate"] = date_str
            else:
                task["arrivaldate"] = date_str

            working_text = working_text.replace(date_match.group(0), ' ')

        # Handle "same day" and remove from working text
        if re.search(r'\bsame\s+day\b', working_text, re.IGNORECASE) and last_date:
            if not task["deadlinedate"] and not task["arrivaldate"]:
                task["arrivaldate"] = last_date
                task["deadlinedate"] = last_date
            elif not task["deadlinedate"]:
                task["deadlinedate"] = last_date
            elif not task["arrivaldate"]:
                task["arrivaldate"] = last_date
            working_text = re.sub(r'\bsame\s+day\b', ' ', working_text, flags=re.IGNORECASE)

        # Extract all times and remove from working text
        time_patterns = []
        time_matches = list(re.finditer(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', working_text, re.IGNORECASE))

        for time_match in time_matches:
            hour = int(time_match.group(1))
            am_pm = time_match.group(3)

            # Convert to 24-hour format
            if am_pm:
                am_pm = am_pm.lower()
                if am_pm == 'pm' and hour != 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0

            # Determine if this is arrival or deadline based on context
            # Look at text BEFORE the time for keywords
            before_time = working_text[:time_match.start()]

            # Check for deadline keywords
            if re.search(r'\b(by|before|complete|deadline|finish)\b', before_time, re.IGNORECASE):
                if task["deadlinetime"] is None:
                    task["deadlinetime"] = hour
            # Check for arrival/start keywords - be more flexible
            elif re.search(r'\b(start|begin|at|from)\b', before_time, re.IGNORECASE):
                if task["arrivaltime"] is None:
                    task["arrivaltime"] = hour
            else:
                # If no keyword found, use position-based logic:
                # First time = arrival, second time = deadline
                if task["arrivaltime"] is None:
                    task["arrivaltime"] = hour
                elif task["deadlinetime"] is None:
                    task["deadlinetime"] = hour

            # Store pattern for removal
            time_patterns.append(time_match.group(0))

        # Remove all extracted times from working text
        for pattern in time_patterns:
            working_text = working_text.replace(pattern, ' ')

        # Check for "anytime" and remove from working text
        if re.search(r'\banytime\b', working_text, re.IGNORECASE):
            task["arrivaltime"] = None
            working_text = re.sub(r'\banytime\b', ' ', working_text, flags=re.IGNORECASE)

        # Remove common scheduling keywords that are not part of task name
        working_text = re.sub(
            r'\b(start|begin|by|before|due|at|on|in|for|complete|finish|the)\b',
            ' ',
            working_text,
            flags=re.IGNORECASE
        )

        # Clean up the task name: remove extra whitespace
        task_name = re.sub(r'\s+', ' ', working_text).strip()

        if task_name:
            task["TaskName"] = task_name
            tasks.append(task)

    # Fallback if no tasks extracted
    return tasks if tasks else [{
        "TaskName": nl_entry[:100],
        "Duration": None,
        "arrivaltime": None,
        "arrivaldate": None,
        "deadlinetime": None,
        "deadlinedate": None,
        "importance": "Medium"
    }]


def run_negotiator(extracted_tasks: List[Dict], nl_entry: str) -> str:
    """
    Negotiator Agent: Checks for missing information.
    """
    tasks_with_issues = []

    for idx, task_info in enumerate(extracted_tasks):
        task_name = task_info.get("TaskName", f"Task {idx + 1}")
        missing_fields = []

        if not task_info.get("Duration"):
            missing_fields.append("Duration")
        if not task_info.get("arrivaldate"):
            missing_fields.append("Start Date")
        if not task_info.get("deadlinedate"):
            missing_fields.append("Deadline Date")
        if task_info.get("deadlinetime") is None and task_info.get("deadlinedate"):
            missing_fields.append("Deadline Time")

        if missing_fields:
            tasks_with_issues.append({
                "name": task_name,
                "missing": missing_fields
            })

    if not tasks_with_issues:
        return "✅ No warnings. All required information is present."

    # Generate warning
    warning_lines = ["⚠️ Missing Information:"]
    for issue in tasks_with_issues:
        warning_lines.append(f"• {issue['name']}: {', '.join(issue['missing'])}")

    return "\n".join(warning_lines) + "\n\nPlease provide these details."


def run_planner(extracted_tasks: List[Dict], nl_entry: str, current_tasks: List[Dict]) -> str:
    """
    Planner Agent: Uses LLM to provide intelligent scheduling suggestions.
    """

    # Format task details for LLM
    task_details = []
    for task in extracted_tasks:
        details = {
            "name": task.get("TaskName"),
            "duration": f"{task.get('Duration')}hrs" if task.get("Duration") else "unknown",
            "starts": f"{task.get('arrivaldate')} at {task.get('arrivaltime')}:00" if task.get(
                'arrivaldate') and task.get('arrivaltime') is not None else "flexible start",
            "deadline": f"{task.get('deadlinedate')} by {task.get('deadlinetime')}:00" if task.get(
                'deadlinedate') and task.get('deadlinetime') is not None else "no deadline",
            "importance": task.get("importance", "Medium")
        }
        task_details.append(details)

    current_date = datetime.now().strftime("%Y-%m-%d %A")
    current_time = datetime.now().strftime("%H:%M")

    prompt = f"""You are an intelligent scheduling assistant analyzing tasks to provide strategic recommendations.

CURRENT DATE/TIME: {current_date} at {current_time}

NEW TASKS TO SCHEDULE:
{json.dumps(task_details, indent=2)}

EXISTING TASKS: {len(current_tasks)} tasks already in schedule

YOUR ANALYSIS GOALS:
1. Identify if any task is complex and should be broken into subtasks
   Example: "write report" → research (1hr), outline (0.5hr), draft (2hrs), review (0.5hr)

2. Check for scheduling conflicts or tight deadlines
   - Is there enough time between start and deadline?
   - Are multiple tasks competing for the same time slot?

3. Suggest optimizations
   - Should tasks be reordered for better flow?
   - Can similar tasks be grouped?
   - Are there productivity tips (e.g., do difficult tasks when fresh)?

4. Consider task dependencies
   - Does one task need to be done before another?

RESPONSE FORMAT:
Provide 2-4 specific, actionable suggestions. Be concrete and helpful.

Start with "💡 Suggestions:" then use bullet points:
• Suggestion 1
• Suggestion 2
• etc.

Keep each suggestion to 1-2 sentences. Focus on practical advice.

Your response:"""

    suggestion_msg = call_ollama(prompt).strip()

    # Ensure proper formatting
    if not suggestion_msg.startswith("💡"):
        suggestion_msg = f"💡 Suggestions:\n{suggestion_msg}"

    # If LLM fails or returns generic response, provide structured fallback
    if len(suggestion_msg) < 50 or "successfully" in suggestion_msg.lower():
        suggestions = ["💡 Suggestions:"]

        # Check for tight deadlines
        for task in extracted_tasks:
            if task.get("Duration") and task.get("arrivaltime") is not None and task.get("deadlinetime") is not None:
                available_time = task.get("deadlinetime") - task.get("arrivaltime")
                if available_time < task.get("Duration"):
                    suggestions.append(
                        f"• ⚠️ '{task.get('TaskName')}' has {available_time}hrs available but needs {task.get('Duration')}hrs - consider adjusting times")

        # Check for task breakdown opportunities
        for task in extracted_tasks:
            if task.get("Duration") and task.get("Duration") >= 3:
                suggestions.append(
                    f"• 📋 Consider breaking '{task.get('TaskName')}' ({task.get('Duration')}hrs) into smaller subtasks for better progress tracking")

        # General productivity tip
        high_priority_tasks = [t for t in extracted_tasks if t.get("importance") == "High"]
        if high_priority_tasks:
            suggestions.append(
                f"• 🎯 You have {len(high_priority_tasks)} high-priority task(s) - consider scheduling these during your peak productivity hours")

        if len(suggestions) == 1:  # Only header
            suggestions.append(f"• ✅ All {len(extracted_tasks)} task(s) look schedulable with current timeframes")
            suggestions.append(f"• 💪 Total workload: {sum(t.get('Duration', 0) for t in extracted_tasks)}hrs")

        suggestion_msg = "\n".join(suggestions)

    return suggestion_msg


def handle_user_response(
        user_response: str,
        previous_suggestion: str,
        task_summary: List[Dict]
) -> Tuple[str, List[Dict]]:
    """
    Handle user's response to suggestions.
    """
    user_lower = user_response.lower().strip()

    if any(word in user_lower for word in ["accept", "yes", "ok", "agree", "sounds good", "perfect", "sure"]):
        return "✅ Great! Your suggestion has been accepted. The tasks are ready to be scheduled.", task_summary
    elif any(word in user_lower for word in ["reject", "no", "decline", "disagree", "don't"]):
        return "❌ Suggestion rejected. Please provide more details.", task_summary
    else:
        return f"💡 Updated Suggestion: I understand you want to modify. {user_response[:100]}", task_summary