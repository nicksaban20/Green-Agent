def search_products(category=None, name=None):
    pass

def place_order(customer_id, product_ids, quantities):
    pass

def return_item(order_id, item_id, reason):
    pass

def check_inventory(product_id):
    pass

def check_policy(policy_type):
    pass

def respond_to_user(message):
    pass

TOOLS = {
    "search_products": {
        "description": "Search for products by category or name",
        "parameters": {
            "category": {"type": "string", "description": "Product category to filter by", "required": False},
            "name": {"type": "string", "description": "Product name to search for", "required": False}
        }
    },
    "place_order": {
        "description": "Place an order for products",
        "parameters": {
            "customer_id": {"type": "integer", "description": "ID of the customer placing the order"},
            "product_ids": {"type": "array", "description": "List of product IDs to order"},
            "quantities": {"type": "array", "description": "List of quantities for each product"}
        }
    },
    "return_item": {
        "description": "Return an item from an order",
        "parameters": {
            "order_id": {"type": "integer", "description": "ID of the order containing the item"},
            "item_id": {"type": "integer", "description": "ID of the specific item to return"},
            "reason": {"type": "string", "description": "Reason for return"}
        }
    },
    "check_inventory": {
        "description": "Check inventory levels for a product",
        "parameters": {
            "product_id": {"type": "integer", "description": "ID of the product to check"}
        }
    },
    "check_policy": {
        "description": "Check store policies",
        "parameters": {
            "policy_type": {"type": "string", "description": "Type of policy to check ('return_window', 'warranty', 'loyalty_discount')"}
        }
    },
    "respond_to_user": {
        "description": "Send a response message to the user",
        "parameters": {
            "message": {"type": "string", "description": "Message to send to the user"}
        }
    }
}