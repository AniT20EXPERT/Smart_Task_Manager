import ollama
import json
import requests


# Define the tool functions
def calculate(operation, num1, num2):
    """Perform basic arithmetic operations"""
    operations = {
        'add': num1 + num2,
        'subtract': num1 - num2,
        'multiply': num1 * num2,
        'divide': num1 / num2 if num2 != 0 else 'Error: Division by zero'
    }
    return operations.get(operation, 'Invalid operation')


def get_weather(city):
    """Get current weather for a city using wttr.in API"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]

            weather_info = {
                'city': city,
                'temperature_c': current['temp_C'],
                'temperature_f': current['temp_F'],
                'condition': current['weatherDesc'][0]['value'],
                'humidity': current['humidity'],
                'wind_speed_kmph': current['windspeedKmph']
            }
            return json.dumps(weather_info)
        else:
            return f"Error: Could not fetch weather for {city}"
    except Exception as e:
        return f"Error: {str(e)}"


# Define tools for Ollama
tools = [
    {
        'type': 'function',
        'function': {
            'name': 'calculate',
            'description': 'Perform basic arithmetic operations (add, subtract, multiply, divide)',
            'parameters': {
                'type': 'object',
                'properties': {
                    'operation': {
                        'type': 'string',
                        'enum': ['add', 'subtract', 'multiply', 'divide'],
                        'description': 'The arithmetic operation to perform'
                    },
                    'num1': {
                        'type': 'number',
                        'description': 'The first number'
                    },
                    'num2': {
                        'type': 'number',
                        'description': 'The second number'
                    }
                },
                'required': ['operation', 'num1', 'num2']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_weather',
            'description': 'Get the current weather for a specific city',
            'parameters': {
                'type': 'object',
                'properties': {
                    'city': {
                        'type': 'string',
                        'description': 'The name of the city'
                    }
                },
                'required': ['city']
            }
        }
    }
]

# Map function names to actual functions
available_functions = {
    'calculate': calculate,
    'get_weather': get_weather
}

# System prompt for Chain of Thought reasoning with strict tool usage
SYSTEM_PROMPT = """You are a helpful assistant with access to tools. You MUST use the available tools for ALL tasks they can handle.

CRITICAL RULES:
1. For ANY arithmetic operation (addition, subtraction, multiplication, division), you MUST call the 'calculate' tool
2. For ANY weather information, you MUST call the 'get_weather' tool
3. DO NOT perform calculations yourself - ALWAYS use the calculate tool, even for simple arithmetic
4. DO NOT provide weather information from memory - ALWAYS use the get_weather tool

When given a complex task:
1. BREAK DOWN the task into clear subtasks
2. Identify which tool is needed for EACH subtask
3. Call tools ONE BY ONE in the correct order
4. Wait for tool results before proceeding
5. Use previous tool results as inputs for subsequent tool calls
6. Synthesize all tool results into a final answer

WORKFLOW:
Step 1: Analyze the user's request and list all subtasks
Step 2: For each subtask, identify the required tool
Step 3: Call the first tool and wait for results
Step 4: Use those results to call the next tool if needed
Step 5: Continue until all subtasks are completed
Step 6: Provide a comprehensive final answer based on ALL tool results

AVAILABLE TOOLS:
- calculate(operation, num1, num2): Use for add, subtract, multiply, divide operations
- get_weather(city): Use for getting current weather information

REMEMBER: You must call these tools explicitly. Never skip tool calls or do the work yourself!
"""


def chat_with_cot_and_tools(user_message, conversation_history=None, max_iterations=10, verbose=True):
    """
    Chat with the model using Chain of Thought and iterative tool calling

    Args:
        user_message: The user's input
        conversation_history: Previous conversation messages
        max_iterations: Maximum number of tool calling iterations to prevent infinite loops
        verbose: Whether to print detailed reasoning steps
    """
    if conversation_history is None:
        conversation_history = [
            {'role': 'system', 'content': SYSTEM_PROMPT}
        ]

    # Add user message to history
    conversation_history.append({
        'role': 'user',
        'content': user_message
    })

    iteration = 0
    tool_calls_made = 0

    while iteration < max_iterations:
        iteration += 1

        if verbose:
            print(f"\n{'=' * 60}")
            print(f"🔄 ITERATION {iteration}")
            print(f"{'=' * 60}")

        # Call the model
        response = ollama.chat(
            model='granite3.2:8b',
            messages=conversation_history,
            tools=tools
        )

        assistant_message = response['message']

        # Show reasoning if present
        if assistant_message.get('content'):
            if verbose:
                print(f"\n💭 Chain of Thought Reasoning:")
                print(f"{assistant_message['content']}\n")

        # Add assistant's response to history
        conversation_history.append(assistant_message)

        # Check if the model wants to use tools
        if assistant_message.get('tool_calls'):
            tool_calls_made += len(assistant_message['tool_calls'])

            if verbose:
                print(f"🔧 Tool Calls Requested: {len(assistant_message['tool_calls'])}")

            # Process each tool call
            for tool_call in assistant_message['tool_calls']:
                function_name = tool_call['function']['name']
                function_args = tool_call['function']['arguments']

                if verbose:
                    print(f"\n  📌 Calling: {function_name}")
                    print(f"  📝 Args: {json.dumps(function_args, indent=2)}")

                # Execute the function
                if function_name in available_functions:
                    function_to_call = available_functions[function_name]
                    function_response = function_to_call(**function_args)

                    if verbose:
                        print(f"  ✅ Result: {function_response}")

                    # Add function response to conversation with reminder to continue using tools
                    conversation_history.append({
                        'role': 'tool',
                        'content': str(function_response)
                    })
                else:
                    error_msg = f"Function {function_name} not found"
                    if verbose:
                        print(f"  ❌ Error: {error_msg}")
                    conversation_history.append({
                        'role': 'tool',
                        'content': error_msg
                    })

            # Add a reminder message after tool execution to prompt for more tool usage if needed
            if iteration < max_iterations:
                conversation_history.append({
                    'role': 'user',
                    'content': 'Based on the tool results above, if you need to perform any calculations or get more data, use the appropriate tools. If all subtasks are complete, provide your final answer.'
                })

            # Continue to next iteration to let model process tool results
            continue
        else:
            # No more tool calls, we have the final answer
            if verbose:
                print(f"\n{'=' * 60}")
                print(f"✨ FINAL ANSWER (Total tool calls made: {tool_calls_made})")
                print(f"{'=' * 60}\n")

            return assistant_message.get('content', ''), conversation_history

    # Max iterations reached
    warning = f"\n⚠️ Reached maximum iterations ({max_iterations}). Returning current response."
    if verbose:
        print(warning)

    return assistant_message.get('content', '') + warning, conversation_history


def main():
    """Main chatbot loop with Chain of Thought and iterative tool calling"""
    print("🤖 Advanced Chatbot with Chain of Thought + Iterative Tool Calling")
    print("=" * 70)
    print("Model: Ollama + Granite 3.2 8B")
    print("Features: Chain of Thought reasoning, Iterative tool calling")
    print("\nAvailable tools:")
    print("  • Calculator (add, subtract, multiply, divide)")
    print("  • Weather (get current weather for any city)")
    print("\nTry complex queries that require multiple steps!")
    print("Examples:")
    print("  - 'Get weather for Paris and London, then calculate the temp difference'")
    print("  - 'Calculate (25 * 4) + (100 / 5), then tell me if that's hotter than NYC'")
    print("\nType 'quit' or 'exit' to end\n")
    print("=" * 70 + "\n")

    conversation_history = [
        {'role': 'system', 'content': SYSTEM_PROMPT}
    ]

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ['quit', 'exit']:
            print("\n👋 Goodbye!")
            break

        if not user_input:
            continue

        try:
            response, conversation_history = chat_with_cot_and_tools(
                user_input,
                conversation_history,
                max_iterations=10,
                verbose=True
            )

            print(f"Assistant: {response}\n")
            print("=" * 70 + "\n")

        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()