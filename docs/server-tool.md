# Step 8: Built-in Server Tool

## Tool chosen
OpenRouter's web search plugin (`:online` model suffix)

## Why
Anthropic's native server-side web search tool isn't available through 
OpenRouter's OpenAI-compatible endpoint, so I used OpenRouter's own 
equivalent. This is useful for triage in cases where a customer references 
something requiring current information (e.g., service status, ongoing 
outages) that isn't in the mock customer/order data.

## How it's used
Implemented as a standalone search_with_web_tool() function using the 
:online model suffix, which triggers OpenRouter's web search automatically 
without a separate tool schema.