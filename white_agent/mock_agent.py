import json
import re
from flask import Flask, request, jsonify
from typing import Dict, Any


class MockWhiteAgent:
    
    def __init__(self):
        self.current_scenario = None
        self.turn_count = 0
        self.available_tools = {}
        
        self.behaviors = {
            "airline_success_1": self._airline_success_simple,
            "airline_failure_1": self._airline_violate_policy,
            "airline_success_2": self._airline_success_with_policy_check,
            "airline_failure_2": self._airline_book_nonexistent,
            "airline_success_3": self._airline_search_and_book,
            "retail_success_1": self._retail_success_simple,
            "retail_failure_1": self._retail_violate_return_policy,
            "retail_success_2": self._retail_success_with_loyalty,
            "retail_failure_2": self._retail_order_insufficient_stock,
            "retail_success_3": self._retail_search_and_order
        }
    
    def get_agent_card(self) -> Dict[str, Any]:
        return {
            "name": "Mock White Agent",
            "description": "Mock agent for τ-bench testing",
            "version": "1.0.0",
            "capabilities": ["tool_use", "conversation"]
        }
    
    def process_message(self, message: str) -> str:
        self.turn_count += 1
        
        # Detect scenario from user goal messages (matching test_cases/*.json)
        if "airline_success_1" in message or "Los Angeles" in message or "fly to Los Angeles" in message:
            self.current_scenario = "airline_success_1"
        elif "airline_failure_1" in message or "Cancel my flight" in message:
            self.current_scenario = "airline_failure_1"
        elif "airline_success_2" in message or "check the cancellation policy" in message:
            self.current_scenario = "airline_success_2"
        elif "airline_failure_2" in message or "Book flight 999" in message or "flight to Mars" in message:
            self.current_scenario = "airline_failure_2"
        elif "airline_success_3" in message or "go to NYC" in message or "NYC" in message:
            self.current_scenario = "airline_success_3"
        elif "retail_success_1" in message or "buy a laptop" in message:
            self.current_scenario = "retail_success_1"
        elif "retail_failure_1" in message or "return this laptop" in message:
            self.current_scenario = "retail_failure_1"
        elif "retail_success_2" in message or "loyalty points" in message:
            self.current_scenario = "retail_success_2"
        elif "retail_failure_2" in message or "buy 100 laptops" in message:
            self.current_scenario = "retail_failure_2"
        elif "retail_success_3" in message or "all electronics" in message:
            self.current_scenario = "retail_success_3"
        
        if "Here's a list of tools" in message:
            self._parse_tools_from_message(message)
            self.turn_count = 1
        
        behavior_func = self.behaviors.get(self.current_scenario, self._default_behavior)
        
        response = behavior_func(message)
        
        return json.dumps(response)
    
    def _parse_tools_from_message(self, message: str):
        json_match = re.search(r'\[(.*?)\]', message, re.DOTALL)
        if json_match:
            try:
                tools_data = json.loads(f"[{json_match.group(1)}]")
                self.available_tools = {tool['name']: tool for tool in tools_data}
            except:
                pass
    
    def _airline_success_simple(self, message: str) -> Dict[str, Any]:
        if self.turn_count == 1:
            return {"name": "search_flights", "kwargs": {"destination": "LAX", "date": "2025-11-01"}}
        elif self.turn_count == 2:
            return {"name": "book_flight", "kwargs": {"flight_id": 101, "user_id": 1}}
        else:
            return {"name": "respond_to_user", "kwargs": {"message": "Your flight has been booked successfully!"}}
    
    def _airline_violate_policy(self, message: str) -> Dict[str, Any]:
        if self.turn_count == 1:
            return {"name": "cancel_booking", "kwargs": {"booking_id": 1}}
        else:
            return {"name": "respond_to_user", "kwargs": {"message": "I tried to cancel but it's not allowed."}}
    
    def _airline_success_with_policy_check(self, message: str) -> Dict[str, Any]:
        if self.turn_count == 1:
            return {"name": "check_policy", "kwargs": {"policy_type": "cancellation"}}
        elif self.turn_count == 2:
            return {"name": "search_flights", "kwargs": {"destination": "LAX", "date": "2025-11-02"}}
        elif self.turn_count == 3:
            return {"name": "book_flight", "kwargs": {"flight_id": 102, "user_id": 2}}
        else:
            return {"name": "respond_to_user", "kwargs": {"message": "Flight booked with policy checked!"}}
    
    def _airline_book_nonexistent(self, message: str) -> Dict[str, Any]:
        if self.turn_count == 1:
            return {"name": "book_flight", "kwargs": {"flight_id": 999, "user_id": 1}}
        else:
            return {"name": "respond_to_user", "kwargs": {"message": "I tried to book but flight doesn't exist."}}
    
    def _airline_search_and_book(self, message: str) -> Dict[str, Any]:
        if self.turn_count == 1:
            return {"name": "search_flights", "kwargs": {"destination": "NYC", "date": "2025-11-01"}}
        elif self.turn_count == 2:
            return {"name": "book_flight", "kwargs": {"flight_id": 103, "user_id": 3}}
        else:
            return {"name": "respond_to_user", "kwargs": {"message": "Found and booked NYC flight!"}}
    
    def _retail_success_simple(self, message: str) -> Dict[str, Any]:
        if self.turn_count == 1:
            return {"name": "search_products", "kwargs": {"name": "laptop"}}
        elif self.turn_count == 2:
            return {"name": "place_order", "kwargs": {"customer_id": 1, "product_ids": [201], "quantities": [1]}}
        else:
            return {"name": "respond_to_user", "kwargs": {"message": "Laptop ordered successfully!"}}
    
    def _retail_violate_return_policy(self, message: str) -> Dict[str, Any]:
        if self.turn_count == 1:
            return {"name": "return_item", "kwargs": {"order_id": 1, "item_id": 1, "reason": "Changed mind"}}
        else:
            return {"name": "respond_to_user", "kwargs": {"message": "I tried to return but it's outside the window."}}
    
    def _retail_success_with_loyalty(self, message: str) -> Dict[str, Any]:
        if self.turn_count == 1:
            return {"name": "check_policy", "kwargs": {"policy_type": "loyalty_discount"}}
        elif self.turn_count == 2:
            return {"name": "search_products", "kwargs": {"name": "mouse"}}
        elif self.turn_count == 3:
            return {"name": "place_order", "kwargs": {"customer_id": 2, "product_ids": [202], "quantities": [1]}}
        else:
            return {"name": "respond_to_user", "kwargs": {"message": "Mouse ordered with loyalty discount!"}}
    
    def _retail_order_insufficient_stock(self, message: str) -> Dict[str, Any]:
        if self.turn_count == 1:
            return {"name": "place_order", "kwargs": {"customer_id": 1, "product_ids": [201], "quantities": [100]}}
        else:
            return {"name": "respond_to_user", "kwargs": {"message": "I tried to order but insufficient stock."}}
    
    def _retail_search_and_order(self, message: str) -> Dict[str, Any]:
        if self.turn_count == 1:
            return {"name": "search_products", "kwargs": {"category": "Electronics"}}
        elif self.turn_count == 2:
            return {"name": "place_order", "kwargs": {"customer_id": 3, "product_ids": [201], "quantities": [1]}}
        else:
            return {"name": "respond_to_user", "kwargs": {"message": "Electronics found and ordered!"}}
    
    def _default_behavior(self, message: str) -> Dict[str, Any]:
        return {"name": "respond_to_user", "kwargs": {"message": "I don't know what to do."}}


app = Flask(__name__)

mock_agent = MockWhiteAgent()


@app.route('/agent-card', methods=['GET'])
def get_agent_card():
    return jsonify(mock_agent.get_agent_card())


@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        response = mock_agent.process_message(message)
        
        return response
        
    except Exception as e:
        return jsonify({"error": str(e)})


def main():
    app.run(host='0.0.0.0', port=8002, debug=False)


if __name__ == "__main__":
    main()
