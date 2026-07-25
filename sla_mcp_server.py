from datetime import datetime, timedelta, timezone
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SLA Server")

# Hours-to-resolve per urgency tier, matching docs/triage-logic.md
SLA_HOURS = {
    "Critical": 1,
    "High": 4,
    "Medium": 24,
    "Low": 72,
}


@mcp.tool()
def check_sla_deadline(urgency: str, created_at: str) -> dict:
    """Compute a ticket's SLA deadline and whether it's already breached.

    Args:
        urgency: One of Critical, High, Medium, Low
        created_at: ISO 8601 timestamp of when the ticket was created
    """
    hours = SLA_HOURS.get(urgency)
    if hours is None:
        raise ValueError(f"Unknown urgency '{urgency}', expected one of {list(SLA_HOURS)}")

    created = datetime.fromisoformat(created_at)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    deadline = created + timedelta(hours=hours)
    remaining = deadline - datetime.now(timezone.utc)

    return {
        "urgency": urgency,
        "sla_hours": hours,
        "deadline": deadline.isoformat(),
        "hours_remaining": round(remaining.total_seconds() / 3600, 2),
        "is_breached": remaining.total_seconds() < 0,
    }


if __name__ == "__main__":
    mcp.run()
