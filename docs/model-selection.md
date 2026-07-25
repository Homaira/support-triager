# Model Selection

## Provider choice
Using OpenRouter instead of direct Anthropic API

## Tier 1: High-volume classification (initial urgency/topic tagging)
Model: anthropic/claude-3-5-haiku (or check OpenRouter's current Haiku slug)
Why: [fast + cheap, used for every incoming message, doesn't need deep reasoning]

## Tier 2: Main triager (tool use, ticket summaries)
Model: anthropic/claude-sonnet-5
Why: [balances quality and cost, handles the tool-calling logic]

## Tier 3: Escalation path (complex/sensitive cases)
Model: anthropic/claude-opus-4.5 (or current Opus slug on OpenRouter)
Why: [used only when Tier 1 flags something as Critical/ambiguous — reasoning quality matters more than cost here]