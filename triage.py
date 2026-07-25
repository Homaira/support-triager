import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from tools import TOOLS, AVAILABLE_FUNCTIONS

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


def execute_tool_call(tool_call_dict):
    func_name = tool_call_dict["name"]
    func_args = json.loads(tool_call_dict["arguments"])
    result = AVAILABLE_FUNCTIONS[func_name](**func_args)

    # Token optimization: don't send full item-level detail back to the model —
    # it only needs status/total/charge_count to make routing decisions
    if func_name == "fetch_order":
        result = {k: v for k, v in result.items() if k != "items"}

    return {
        "role": "tool",
        "tool_call_id": tool_call_dict["id"],
        "content": json.dumps(result)
    }


def stream_and_check_tools(messages, max_tokens=1200):
    """Stream text as it arrives; also collect any tool calls from the stream."""
    full_text = ""
    tool_calls_accum = {}

    with client.chat.completions.create(
        model="anthropic/claude-sonnet-5",
        messages=messages,
        tools=TOOLS,
        # max_tokens=1200,
        max_tokens=max_tokens,
        stream=True
    ) as stream:
        for chunk in stream:
            delta = chunk.choices[0].delta

            if delta.content:
                print(delta.content, end="", flush=True)
                full_text += delta.content

            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_calls_accum:
                        tool_calls_accum[idx] = {"id": tc_delta.id, "name": "", "arguments": ""}
                    if tc_delta.function.name:
                        tool_calls_accum[idx]["name"] += tc_delta.function.name
                    if tc_delta.function.arguments:
                        tool_calls_accum[idx]["arguments"] += tc_delta.function.arguments

    print()
    return full_text, tool_calls_accum


def search_with_web_tool(query: str):
    """Uses OpenRouter's built-in web search plugin to answer a query with live info."""
    response = client.chat.completions.create(
        model="anthropic/claude-sonnet-5:online",
        messages=[{"role": "user", "content": query}],
        max_tokens=500
    )
    return response.choices[0].message.content


def triage_message(user_message: str):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    while True:
        # full_text, tool_calls_accum = stream_and_check_tools(messages)
        full_text, tool_calls_accum = stream_and_check_tools(messages, max_tokens=900)

        if not tool_calls_accum:
            return full_text  # done — no tools needed, already streamed live

        # Rebuild the assistant's turn (needed so the model "remembers" it asked for tools)
        messages.append({
            "role": "assistant",
            "content": full_text or None,
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]}
                }
                for tc in tool_calls_accum.values()
            ]
        })

        with ThreadPoolExecutor() as executor:
            tool_results = list(executor.map(execute_tool_call, tool_calls_accum.values()))

        messages.extend(tool_results)


if __name__ == "__main__":
    sample = "My last order #4521 never arrived and I've been charged twice."
    result = triage_message(sample)
    print("\n\nFinal result:", result)

    print("\n--- Second test: parallel tool calls ---\n")
    sample2 = "I'm customer cust_882, and I want to check on order ord_991 — is it shipped yet?"
    result2 = triage_message(sample2)
    print("\n\nFinal result:", result2)

    print("\n--- Step 8: web search test ---\n")
    answer = search_with_web_tool("What is the current status of the Anthropic API — any reported outages today?")
    print(answer)