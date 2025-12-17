import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file in project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, '.env'))

import anthropic

app = Flask(__name__)

# Initialize Anthropic client
# Expects ANTHROPIC_API_KEY in environment variables or .env file
client = anthropic.Anthropic()
SYSTEM_PROMPT = """You are a tool-calling assistant. Respond with ONLY a JSON tool call in <json>...</json> tags.

STRICT RULES:
1. Output ONLY: <json>{"name": "...", "kwargs": {...}}</json>
2. NO text before or after the json block
3. In respond_to_user, message must be UNDER 30 characters, no special punctuation
4. Complete ALL actions before responding to user

=== AIRLINE TOOLS ===
<json>{"name": "search_flights", "kwargs": {"destination": "LAX", "date": "2025-11-01"}}</json>
<json>{"name": "book_flight", "kwargs": {"flight_id": 101, "user_id": 1}}</json>
<json>{"name": "cancel_booking", "kwargs": {"booking_id": 1}}</json>
<json>{"name": "check_policy", "kwargs": {"policy_type": "cancellation"}}</json>

=== RETAIL TOOLS ===
<json>{"name": "search_products", "kwargs": {"name": "laptop"}}</json>
<json>{"name": "search_products", "kwargs": {"category": "Electronics"}}</json>
<json>{"name": "place_order", "kwargs": {"customer_id": 1, "product_ids": [201], "quantities": [1]}}</json>

=== RESPOND (use short messages!) ===
<json>{"name": "respond_to_user", "kwargs": {"message": "Flight booked!"}}</json>
<json>{"name": "respond_to_user", "kwargs": {"message": "Order placed!"}}</json>
<json>{"name": "respond_to_user", "kwargs": {"message": "Cannot cancel."}}</json>

WORKFLOWS:
- Book flight: search_flights -> book_flight -> respond_to_user
- Buy product: search_products -> place_order -> respond_to_user
- Check policy: check_policy -> respond_to_user

CRITICAL: Use flight_id/product_id from tool results. Customer/user ID defaults to 1.
"""

class ClaudeAgent:
    def __init__(self):
        self.history = []

    def reset(self):
        self.history = []

    def process_message(self, message):
        self.history.append({"role": "user", "content": message})

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            temperature=0.0,
            system=SYSTEM_PROMPT,
            messages=self.history
        )

        content = response.content[0].text
        self.history.append({"role": "assistant", "content": content})
        return content

agent = ClaudeAgent()

@app.route('/agent-card', methods=['GET'])
def get_agent_card():
    return jsonify({
        "name": "Claude White Agent",
        "capabilities": ["llm", "tool_use"]
    })

@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        message = data.get('message', '')

        # Check if this is a new task
        if "Here's a list of tools" in message:
            agent.reset()

        response_text = agent.process_message(message)
        # Return as plain text, not JSON-encoded
        return response_text, 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/.well-known/agent-card.json', methods=['GET'])
def get_agent_card_well_known():
    return jsonify({
        "name": "Claude White Agent",
        "capabilities": ["llm", "tool_use"]
    })

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('AGENT_PORT', '8002'))
    app.run(host=host, port=port)
