def search_flights(destination, date):
    pass

def book_flight(flight_id, user_id):
    pass

def cancel_booking(booking_id):
    pass

def check_policy(policy_type):
    pass

def respond_to_user(message):
    pass

TOOLS = {
    "search_flights": {
        "description": "Search for available flights to a destination on a specific date",
        "parameters": {
            "destination": {"type": "string", "description": "Airport code (e.g., 'LAX', 'NYC', 'CHI')"},
            "date": {"type": "string", "description": "Date in YYYY-MM-DD format"}
        }
    },
    "book_flight": {
        "description": "Book a flight for a user",
        "parameters": {
            "flight_id": {"type": "integer", "description": "ID of the flight to book"},
            "user_id": {"type": "integer", "description": "ID of the user making the booking"}
        }
    },
    "cancel_booking": {
        "description": "Cancel an existing booking",
        "parameters": {
            "booking_id": {"type": "integer", "description": "ID of the booking to cancel"}
        }
    },
    "check_policy": {
        "description": "Check airline policies",
        "parameters": {
            "policy_type": {"type": "string", "description": "Type of policy to check ('cancellation', 'change_fee', 'booking_limit')"}
        }
    },
    "respond_to_user": {
        "description": "Send a response message to the user",
        "parameters": {
            "message": {"type": "string", "description": "Message to send to the user"}
        }
    }
}