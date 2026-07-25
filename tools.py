def lookup_customer(customer_id: str) -> dict:
    """Mock customer lookup — replace with real DB call later."""
    return {
        "customer_id": customer_id,
        "name": "Jordan Ellis",
        "email": "jordan.ellis@example.com",
        "tier": "gold",
        "signup_date": "2022-03-14"
    }

def fetch_order(order_id: str) -> dict:
    """Mock order lookup."""
    return {
        "order_id": order_id,
        "status": "delivered",
        "items": [
            {"sku": "WBH-100", "name": "Wireless Headphones", "qty": 1, "price": 79.99},
            {"sku": "USB-C-2M", "name": "USB-C Cable 2m", "qty": 2, "price": 9.99}
        ],
        "total": 99.97,
        "charge_count": 2,
        "delivery_date": "2026-07-20"
    }

def create_ticket(summary: str, urgency: str, topic: str) -> dict:
    """Mock ticket creation."""
    return {
        "ticket_id": "TCK-001",
        "status": "created",
        "summary": summary,
        "urgency": urgency,
        "topic": topic
    }

# OpenAI/OpenRouter tool-schema format — this is what teaches Claude what tools exist
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_customer",
            "description": "Look up a customer's account info by their customer ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The customer's ID"}
                },
                "required": ["customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_order",
            "description": "Look up an order's status, items, and total by its order ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order's ID"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create a support ticket to escalate an issue for human follow-up",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "A short summary of the customer's issue"},
                    "urgency": {"type": "string", "description": "How urgent the issue is, e.g. 'low', 'medium', 'high'"},
                    "topic": {"type": "string", "description": "The general category of the issue, e.g. 'billing', 'shipping', 'returns'"}
                },
                "required": ["summary", "urgency", "topic"]
            }
        }
    },
]

AVAILABLE_FUNCTIONS = {
    "lookup_customer": lookup_customer,
    "fetch_order": fetch_order,
    "create_ticket": create_ticket,
}
