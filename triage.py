import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from tools import TOOLS, AVAILABLE_FUNCTIONS
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

SYSTEM_PROMPT = """You are a customer support triager. For each message, determine:

1. Urgency: Critical (service down, security issue, payment failure), 
   High, Medium, or Low
2. Topic: Billing, Technical, Account/Access, Feature Request, or General
3. Route: which team should handle it, based on urgency and topic

Use the lookup_customer and fetch_order tools when the message references 
a customer or order, to get more context before deciding. Use create_ticket 
once you've determined the routing, to formally escalate the issue."""

def execute_tool_call(tool_call):
    print(f"Executing: {tool_call.function.name}")
    func_name = tool_call.function.name
    func_args = json.loads(tool_call.function.arguments)
    result = AVAILABLE_FUNCTIONS[func_name](**func_args)
    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(result)
    }



def triage_message(user_message: str):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    while True:
        response = client.chat.completions.create(
            model="anthropic/claude-sonnet-5",
            messages=messages,
            tools=TOOLS,
            max_tokens=1200
        )
        reply = response.choices[0].message

        if not reply.tool_calls:
            return reply

        messages.append(reply)

        # for tool_call in reply.tool_calls:
        #     func_name = tool_call.function.name
        #     func_args = json.loads(tool_call.function.arguments)
        #     result = AVAILABLE_FUNCTIONS[func_name](**func_args)

        #     messages.append({
        #         "role": "tool",
        #         "tool_call_id": tool_call.id,
        #         "content": json.dumps(result)
        #     })

        # Run independent tool calls concurrently instead of one-by-one
        with ThreadPoolExecutor() as executor:
            tool_results = list(executor.map(execute_tool_call, reply.tool_calls))

        messages.extend(tool_results)


if __name__ == "__main__":
    sample = "My last order #4521 never arrived and I've been charged twice."
    result = triage_message(sample)
    print(result)

    print("\n--- Second test: parallel tool calls ---\n")
    sample2 = "I'm customer cust_882, and I want to check on order ord_991 — is it shipped yet?"
    result2 = triage_message(sample2)
    print(result2)