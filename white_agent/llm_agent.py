import os
import json
from flask import Flask, request, jsonify
import anthropic

app = Flask(__name__)

# Initialize Anthropic client
# Expects ANTHROPIC_API_KEY in environment variables
client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a helpful assistant that can use tools.
You have access to a set of tools. You must respond by calling these tools to help the user.
To call a tool, you MUST wrap the JSON tool call in <json>...</json> tags.
Do not output any other text outside of the <json> tags when calling a tool, unless you are also responding to the user with a message.

Example tool calls:

1. Search for flights:
<json>{"name": "search_flights", "kwargs": {"destination": "LAX", "date": "2025-11-01"}}</json>

2. Respond to the user:
<json>{"name": "respond_to_user", "kwargs": {"message": "I have booked your flight."}}</json>

Always use the <json> tags for tool calls.
"""

class ClaudeAgent:
    def __init__(self):
        self.history = []

    def reset(self):
        self.history = []

    def process_message(self, message):
        self.history.append({"role": "user", "content": message})

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
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
        return jsonify(response_text)
        
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
