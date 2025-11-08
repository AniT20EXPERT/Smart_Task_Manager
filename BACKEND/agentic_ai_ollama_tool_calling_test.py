import json
import ollama


# ========================================
# 1️⃣ Tool Functions
# ========================================
def calculator(operation: str, a: float, b: float) -> dict:
    """Perform a basic arithmetic operation between two numbers."""
    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
            # result = 69
        elif operation == "divide":
            result = a / b if b != 0 else float('inf')
        else:
            return {"error": f"Unknown operation '{operation}'."}
        return {"operation": operation, "a": a, "b": b, "result": result}
    except Exception as e:
        return {"error": str(e)}


# ========================================
# 2️⃣ Tool Registry (Dynamic)
# ========================================
TOOLS = {
    "calculator": calculator,
    # Add more tools here as needed
}

# Tool definitions for Ollama
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform arithmetic operations (add, subtract, multiply, divide)",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "The arithmetic operation to perform"
                    },
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["operation", "a", "b"]
            }
        }
    }
]

# ========================================
# 3️⃣ System Prompt
# ========================================
system_prompt = """
You are CalcMind — an intelligent math assistant with chain-of-thought reasoning.

When solving problems:
1. Break down complex problems into steps
2. Use the calculator tool for each calculation
3. After getting results, continue reasoning if more steps are needed
4. Provide clear final answers

For multi-part questions, solve each part sequentially.
"""

# ========================================
# 4️⃣ Conversation Memory
# ========================================
conversation = [{"role": "system", "content": system_prompt}]


# ========================================
# 5️⃣ Process Tool Calls with Native API
# ========================================
def process_tool_calls(max_iterations=10):
    """Process tool calls using Ollama's native tool-calling API."""
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        print(f"\n{'=' * 60}")
        print(f"Iteration {iteration}")
        print('=' * 60)

        # Call model with tools enabled
        response = ollama.chat(
            model="granite3.2:8b",
            messages=conversation,
            tools=TOOL_DEFINITIONS,
        )

        message = response["message"]

        # Check if model wants to use tools
        if message.get("tool_calls"):
            # Model requested tool calls
            conversation.append(message)

            for tool_call in message["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = tool_call["function"]["arguments"]

                print(f"\n⚙️  Tool Call: {tool_name}")
                print(f"📋 Arguments: {json.dumps(tool_args, indent=2)}")

                # Execute the tool
                if tool_name in TOOLS:
                    result = TOOLS[tool_name](**tool_args)
                    print(f"🧮 Result: {json.dumps(result, indent=2)}")

                    # Add tool response to conversation
                    conversation.append({
                        "role": "tool",
                        "content": json.dumps(result),
                    })
                else:
                    error_result = {"error": f"Tool '{tool_name}' not found"}
                    print(f"❌ Error: {error_result}")
                    conversation.append({
                        "role": "tool",
                        "content": json.dumps(error_result),
                    })

            # Continue loop - model will process tool results and decide next step
            continue

        else:
            # No tool calls - final answer
            content = message.get("content", "")
            print(f"\n✅ Final Answer:\n{content}")
            conversation.append(message)
            break

    if iteration >= max_iterations:
        print("\n⚠️  Max iterations reached. Stopping.")


# ========================================
# 6️⃣ Chat Loop
# ========================================
if __name__ == "__main__":
    print("🧮 CalcMind (Native Tool-Calling API)")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("\n💬 You: ")
        if user_input.lower() == "exit":
            break

        conversation.append({"role": "user", "content": user_input})
        process_tool_calls()

        print("\n" + "=" * 60 + "\n")