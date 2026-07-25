# Model Selection

## Provider choice
Using OpenRouter instead of direct Anthropic API. OpenRouter's OpenAI-compatible
endpoint made local development access simpler given account/billing setup
constraints, at the cost of losing Anthropic's native tool-call format and
MCP connector (worked around manually in Steps 9-11).

## Intended tiering strategy

**Tier 1 — High-volume classification (initial urgency/topic tagging)**
Model: claude-haiku-4-5 (fastest, cheapest Anthropic tier)
Why: this step runs on every single incoming message, and the classification
task itself is narrow and well-specified (pick from a fixed set of urgency/topic
labels) — it doesn't need a large model's reasoning depth, so cost and latency
matter more than capability here.

**Tier 2 — Main triager (tool use, ticket summaries)**
Model: claude-sonnet-5
Why: this step has to decide *which* tools to call and interpret their results
correctly (e.g. recognizing that a delivered order with 2 charges is a billing
issue, not just a shipping one) — a mid-tier model balances that reasoning
requirement against cost, since it runs at least once, often twice, per message.

**Tier 3 — Escalation path (complex/sensitive cases)**
Model: claude-opus-4-8
Why: reserved for cases Tier 1 flags as Critical or ambiguous — situations where
a misrouted ticket is costly (e.g. a security issue sent to the wrong team) and
reasoning quality should outweigh cost/latency concerns.

## Current implementation note

`triage.py` currently uses a single model (`claude-sonnet-5`) for all rounds,
rather than the three-tier routing above. Given time constraints, the tiering
logic itself (a lightweight classification pass to decide which downstream tier
to route to) wasn't implemented. The justification above reflects the intended
design; wiring an actual `if classification == "Critical": use_opus()` routing
step would be the direct next iteration on this system.