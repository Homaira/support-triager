# Token Optimization

## Changes made

1. **Reduced max_tokens per round** — attempted 600 tokens (down from 1200), 
   but this caused truncated tool-call JSON when the model produced both 
   explanatory text and a tool call in the same turn, raising a 
   JSONDecodeError. Settled on 900 as a working middle ground — still a 
   25% reduction from the original, with no observed truncation across 
   test cases.
   Effect: moderate token savings; discovered that tool-calling rounds 
   aren't always "text-free," so budget can't be cut as aggressively as 
   pure tool-only rounds would suggest.

2. **Trimmed tool result payloads** — stripped full item-level detail from 
   fetch_order results before sending back to the model, keeping only 
   status/total/charge_count. 
   Effect: smaller context per round, especially compounds across 
   multi-round tool use.

3. **Tightened system prompt wording** — removed redundant phrasing in 
   the rubric instructions. 
   Effect: small per-call savings, but multiplied across every incoming 
   message since the system prompt is sent on every call.

## Trade-offs
[One sentence: e.g. "Reducing max_tokens risks truncation on more complex 
cases; if triage responses start getting cut off, this should be raised 
back up for the final round specifically."]