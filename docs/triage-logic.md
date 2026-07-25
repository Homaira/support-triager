# Triage Logic

## Categorization Dimensions

**Urgency:** Critical / High / Medium / Low
- Critical: service down, security issue, payment failure
- High: significant customer impact, but not a full outage or security/payment issue
- Medium: real issue, no immediate business-critical impact
- Low: general questions, minor requests, no urgency

**Topic:**
- Billing
- Technical/Bug
- Account/Access
- Feature Request
- General

**Routing team:** determined jointly from urgency and topic — the model is instructed
to reason about both together rather than following a fixed lookup table, so it can
handle cases that span more than one category (e.g. a billing error tied to a
delivery dispute, as in the example below).

## Implementation

This rubric is implemented directly as the system prompt in `triage.py`:


The prompt also instructs the model to use tools (`lookup_customer`, `fetch_order`)
to gather context *before* deciding, rather than triaging on the raw message text
alone — this lets urgency/topic decisions be grounded in real account and order
data (e.g. an actual duplicate-charge count) rather than inferred from wording.

## Example (real output, from testing)
Message: *"My last order #4521 never arrived and I've been charged twice."*

- The model called `fetch_order("4521")`, which returned `status: delivered`,
  `charge_count: 2`, `total: 99.97`
- **Urgency:** High — duplicate billing plus an unresolved delivery discrepancy
- **Topic:** Billing (with a delivery discrepancy noted)
- **Route:** Billing/Payments team, with a note for Logistics to verify delivery
- The model then called `create_ticket(...)` to formally escalate, referencing the
  real ticket ID and order data in its final customer-facing response