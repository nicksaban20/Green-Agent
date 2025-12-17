import json
import logging
import uuid
import re
from typing import Dict, Any, Optional, List
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from green_agent.environment import Environment

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_tags(str_with_tags: str) -> Dict[str, str]:
    """the target str contains tags in the format of <tag_name> ... </tag_name>, parse them out and return a dict"""
    tags = re.findall(r"<(.*?)>(.*?)</\1>", str_with_tags, re.DOTALL)
    return {tag: content.strip() for tag, content in tags}

class GreenAgent:
    
    def __init__(self, domains_path: str):
        self.domains_path = domains_path
        self.current_env = None
        self.white_agent_url = None
        self.scenario = None
        self.max_turns = 20
        self.context_id = None
        
    def get_agent_card(self) -> Dict[str, Any]:
        return {
            "name": "τ-bench Green Agent",
            "description": "Evaluates agents using τ-bench benchmark for tool-use capabilities in airline and retail domains",
            "version": "1.0.0",
            "url": f"https://{os.getenv('CLOUDRUN_HOST')}" if os.getenv("CLOUDRUN_HOST") else "http://localhost:8001",
            "capabilities": {
                "streaming": False,
                "pushNotifications": False
            },
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
            "skills": [
                {
                    "id": "tau-bench-evaluation",
                    "name": "τ-bench Evaluation",
                    "description": "Evaluate agent tool-use capabilities in airline and retail domains",
                    "tags": ["evaluation", "benchmark", "tool-use"],
                    "examples": ["""    
Your task is to instantiate tau-bench to test the agent located at:
<white_agent_url>
http://localhost:8002/
</white_agent_url>
You should use the following env configuration:
<env_config>
{
  "env": "retail",
  "user_strategy": "llm",
  "user_model": "claude-sonnet-4-20250514",
  "user_provider": "anthropic",
  "task_split": "test",
  "task_ids": [
    0
  ]
}
</env_config>
    """]
                }
            ],
            "supported_domains": ["airline", "retail"],
            "metrics": ["success_rate", "average_completion_time", "turns_per_task"],
            "contact": "agentbeats@berkeley.edu"
        }
    
    def start_evaluation(self, domain: str, scenario_id: str, white_agent_url: str, context_id: Optional[str] = None) -> Dict[str, Any]:
        self.white_agent_url = white_agent_url
        self.scenario = scenario_id
        self.context_id = context_id or str(uuid.uuid4())
        
        logger.info(f"Starting evaluation: domain={domain}, scenario={scenario_id}, context_id={self.context_id}")
        
        scenario_path = os.path.join(
            os.path.dirname(self.domains_path), 
            "test_cases", 
            f"{domain}_scenarios.json"
        )
        
        with open(scenario_path, 'r') as f:
            scenarios = json.load(f)
        
        scenario = next((s for s in scenarios if s['id'] == scenario_id), None)
        if not scenario:
            logger.error(f"Scenario {scenario_id} not found")
            return {"error": f"Scenario {scenario_id} not found"}
        
        logger.info(f"Loaded scenario: {scenario.get('description')}")
        
        domain_path = os.path.join(self.domains_path, domain)
        self.current_env = Environment(domain, domain_path)
        
        if not self.current_env.validate_setup():
            logger.error("Environment validation failed")
            return {"error": "Environment validation failed"}
        
        if 'initial_state' in scenario:
            self._set_initial_state(scenario['initial_state'])
        
        start_time = time.time()
        result = self._run_conversation(scenario)
        end_time = time.time()
        
        goal_state = scenario.get('goal_state', {})
        goal_achieved = self.current_env.evaluate_success(goal_state)
        
        # expected_success indicates if this is a success or failure test case
        # Success scenarios (expected_success=True): pass when goal is achieved
        # Failure scenarios (expected_success=False): always show as failed (they test bad behavior)
        expected_success = scenario.get('expected_success', True)
        
        if expected_success:
            # Success scenario: pass if goal was achieved
            test_passed = goal_achieved
        else:
            # Failure scenario: these test cases are designed to fail
            # They demonstrate what happens when the agent makes mistakes
            test_passed = False
        
        logger.info(f"Evaluation complete: goal_achieved={goal_achieved}, expected_success={expected_success}, test_passed={test_passed}, turns={result.get('turns', 0)}, time={end_time - start_time:.2f}s")
        
        if self.current_env:
            self.current_env.close()
        
        return {
            "success": test_passed,
            "goal_achieved": goal_achieved,
            "expected_success": expected_success,
            "turns": result.get('turns', 0),
            "time_used": end_time - start_time,
            "scenario": scenario_id,
            "domain": domain,
            "conversation_history": self.current_env.conversation_history if self.current_env else []
        }
    
    def run_all_scenarios(self, white_agent_url: str) -> Dict[str, Any]:
        """Run all predefined scenarios and return aggregated metrics."""
        scenarios = [
            ("airline", "airline_success_1"),
            ("airline", "airline_failure_1"),
            ("airline", "airline_success_2"),
            ("airline", "airline_failure_2"),
            ("airline", "airline_success_3"),
            ("retail", "retail_success_1"),
            ("retail", "retail_failure_1"),
            ("retail", "retail_success_2"),
            ("retail", "retail_failure_2"),
            ("retail", "retail_success_3")
        ]
        
        results = []
        total_time = 0
        success_count = 0
        
        logger.info(f"Starting batch evaluation of {len(scenarios)} scenarios")
        
        for domain, scenario_id in scenarios:
            logger.info(f"Running scenario: {domain}/{scenario_id}")
            
            try:
                result = self.start_evaluation(domain, scenario_id, white_agent_url)
                
                if result.get('success'):
                    success_count += 1
                
                total_time += result.get('time_used', 0)
                
                results.append({
                    "domain": domain,
                    "scenario": scenario_id,
                    "success": result.get('success'),
                    "time_used": result.get('time_used'),
                    "turns": result.get('turns')
                })
                
            except Exception as e:
                logger.error(f"Failed scenario {domain}/{scenario_id}: {e}")
                results.append({
                    "domain": domain,
                    "scenario": scenario_id,
                    "success": False,
                    "error": str(e)
                })
        
        success_rate = success_count / len(scenarios) if scenarios else 0
        avg_time = total_time / len(scenarios) if scenarios else 0
        
        logger.info(f"Batch evaluation complete. Success rate: {success_rate:.2%}")
        
        return {
            "aggregate_metrics": {
                "success_rate": success_rate,
                "success_count": success_count,
                "total_scenarios": len(scenarios),
                "average_time": avg_time,
                "total_time": total_time
            },
            "individual_results": results
        }
    
    def _set_initial_state(self, initial_state: Dict[str, Any]):
        if self.current_env:
            self.current_env.reset_to_state(initial_state)
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from response, handling <json>...</json> tags."""
        json_match = re.search(r'<json>(.*?)</json>', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            # Handle newlines inside JSON strings by properly escaping them
            # Replace literal newlines with escaped newlines for JSON parsing
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Try to fix common issues with newlines in strings
                # This handles cases where Claude puts actual newlines in message content
                fixed_str = re.sub(r'(?<!\\)\n', r'\\n', json_str)
                return json.loads(fixed_str)
        
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    fixed_str = re.sub(r'(?<!\\)\n', r'\\n', json_str)
                    return json.loads(fixed_str)
            raise
    
    def _run_conversation(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        user_goal = scenario.get('user_goal', '')
        
        try:
            initial_message = self._create_initial_message(user_goal)
            response = self._send_to_white_agent(initial_message)
        except Exception as e:
            logger.error(f"Failed to send initial message: {e}")
            return {"error": f"Failed to start conversation: {e}", "turns": 0}
        
        turns = 0
        conversation_complete = False
        
        while turns < self.max_turns and not conversation_complete:
            turns += 1
            logger.debug(f"Turn {turns}/{self.max_turns}")
            
            try:
                response_data = self._extract_json_from_response(response)
                tool_name = response_data.get('name')
                tool_kwargs = response_data.get('kwargs', {})
                
                logger.debug(f"White agent called tool: {tool_name}")
                
                if tool_name == 'respond_to_user':
                    conversation_complete = True
                    result = self.current_env.execute_tool(tool_name, **tool_kwargs)
                    logger.info(f"Conversation completed in {turns} turns")
                else:
                    result = self.current_env.execute_tool(tool_name, **tool_kwargs)
                    response = self._send_tool_result_to_white_agent(result)
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from white agent: {e}")
                logger.error(f"Response was: {response[:200]}")
                return {"error": "Invalid JSON response from white agent", "turns": turns}
            except Exception as e:
                logger.error(f"Error during conversation turn {turns}: {e}")
                return {"error": str(e), "turns": turns}
        
        if not conversation_complete:
            logger.warning(f"Conversation did not complete within {self.max_turns} turns")
        
        return {"turns": turns, "completed": conversation_complete}
    
    def _create_initial_message(self, user_goal: str) -> str:
        tools_info = []
        for tool_name, tool_info in self.current_env.tools.items():
            tools_info.append({
                "name": tool_name,
                "description": tool_info["description"],
                "parameters": tool_info["parameters"]
            })
        
        message = f"""Here's a list of tools you can use (you can use at most one tool at a time):
{json.dumps(tools_info, indent=2)}



Please respond in the JSON format. Please wrap the JSON part with <json>...</json> tags.
The JSON should contain:

- "name": the tool call function name, or "respond_to_user" if you want to respond directly.

- "kwargs": the arguments for the tool call, or {{"message": "your message here"}} if you want to respond directly.



Next, I'll provide you with the user message and tool call results.

User message: {user_goal}"""
        
        return message
    
    def _send_to_white_agent(self, message: str) -> str:
        """Send a message to the white agent and handle both A2A and direct response formats."""
        try:
            payload = {
                "message": message
            }
            
            if self.context_id:
                payload["context_id"] = self.context_id
            
            logger.debug(f"Sending to white agent: {message[:100]}...")
            
            response = requests.post(
                f"{self.white_agent_url}/send-message",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            response_text = response.text
            logger.debug(f"Received from white agent: {response_text[:100]}...")
            
            try:
                response_json = json.loads(response_text)
                
                if 'result' in response_json:
                    result = response_json['result']
                    if 'parts' in result and len(result['parts']) > 0:
                        first_part = result['parts'][0]
                        if 'text' in first_part:
                            return first_part['text']
                        elif 'root' in first_part and 'text' in first_part['root']:
                            return first_part['root']['text']
                
                if 'message' in response_json:
                    return response_json['message']
                    
            except json.JSONDecodeError:
                pass
            
            return response_text
            
        except requests.RequestException as e:
            logger.error(f"Failed to communicate with white agent: {e}")
            raise Exception(f"Failed to communicate with white agent: {e}")
    
    def _send_tool_result_to_white_agent(self, tool_result: Dict[str, Any]) -> str:
        message = f"Tool result: {json.dumps(tool_result)}"
        return self._send_to_white_agent(message)




app = Flask(__name__)

green_agent = None





@app.route('/agent-card', methods=['GET'])
def get_agent_card():
    return jsonify(green_agent.get_agent_card())

@app.route('/.well-known/agent-card.json', methods=['GET'])
def get_agent_card_well_known():
    return jsonify(green_agent.get_agent_card())

@app.route('/reset', methods=['POST'])
def reset_agent():
    """Reset the agent state - required by AgentBeats for assessments."""
    global green_agent
    logger.info("Agent reset requested")
    # Reinitialize the agent
    domains_path = os.path.join(os.path.dirname(__file__), "..", "domains")
    green_agent = GreenAgent(domains_path)
    return jsonify({"status": "reset", "ready": True})

@app.route('/status', methods=['GET'])
def get_status():
    """Return agent status - required by AgentBeats for assessments."""
    return jsonify({"status": "running", "ready": True})


@app.route('/', methods=['GET', 'POST'])
def root_handler():
    if request.method == 'GET':
        return jsonify({"status": "running", "ready": True})
        
    # Handle POST - forward to send_message logic
    return send_message()

@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        logger.info(f"Received data keys: {list(data.keys())}")
        
        # Handle JSON-RPC style wrapper if present
        if "params" in data and "method" in data:
            logger.info("Detected JSON-RPC format")
            data = data["params"]
            
        message = data.get('message', '')
        context_id = data.get('context_id')
        
        logger.info(f"Received message: {message[:200]}...")
        
        # Check for AgentBeats XML tags format
        tags = parse_tags(message)
        if "white_agent_url" in tags and "env_config" in tags:
            white_agent_url = tags["white_agent_url"]
            env_config = json.loads(tags["env_config"])
            
            domain = env_config.get("env", "retail")
            task_ids = env_config.get("task_ids", [0])
            
            # Load scenarios for the domain
            scenario_path = os.path.join(
                os.path.dirname(green_agent.domains_path), 
                "test_cases", 
                f"{domain}_scenarios.json"
            )
            
            if not os.path.exists(scenario_path):
                return jsonify({"error": f"Unknown domain: {domain}"}), 400
                
            with open(scenario_path, 'r') as f:
                scenarios = json.load(f)
            
            results = []
            for task_idx in task_ids:
                if 0 <= task_idx < len(scenarios):
                    scenario = scenarios[task_idx]
                    scenario_id = scenario["id"]
                    
                    # Run evaluation
                    logger.info(f"Running task {task_idx} (scenario: {scenario_id})")
                    result = green_agent.start_evaluation(domain, scenario_id, white_agent_url, context_id)
                    results.append(result)
                else:
                    logger.warning(f"Task index {task_idx} out of range for domain {domain}")
            
            # Format response for AgentBeats
            if not results:
                return jsonify({"status": "error", "message": "No valid tasks executed"}), 400
                
            # Aggregate results (using the last one for main status, similar to reference)
            last_result = results[-1]
            success = last_result["success"]
            result_emoji = "✅" if success else "❌"
            
            response_text = f"Finished. White agent success: {result_emoji}\nMetrics: {json.dumps(last_result)}\n"
            return jsonify({"message": response_text})

        
        if "Run all scenarios" in message or "--all" in message:
            white_agent_url = None
            for line in message.split('\n'):
                if "White agent URL:" in line:
                    white_agent_url = line.split("White agent URL:")[1].strip()
                    break
            
            if not white_agent_url:
                # Try to extract from tags if mixed format
                if "white_agent_url" in tags:
                    white_agent_url = tags["white_agent_url"]
                else:
                    return jsonify({"error": "White agent URL not found"}), 400
            
            results = green_agent.run_all_scenarios(white_agent_url)
            return jsonify(results)
            
        elif "Run tau-bench evaluation" in message:
            # Parse domain and scenario keys
            domain = "airline" # default
            scenario = "airline_success_1" # default
            white_agent_url = "http://localhost:8002"
            
            parts = message.split(',')
            for part in parts:
                if "domain:" in part:
                    domain = part.split(":")[1].strip()
                if "scenario:" in part:
                    scenario = part.split(":")[1].strip()
            
            # Also try to find URL in lines
            for line in message.split('\n'):
                if "White agent URL:" in line:
                    white_agent_url = line.split("White agent URL:")[1].strip()
                    break
            
            result = green_agent.start_evaluation(domain, scenario, white_agent_url, context_id)
            return jsonify(result)
            
        else:
            return jsonify({"error": "Unknown message format. Expected 'Run tau-bench evaluation' or 'Run all scenarios'"})
            
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return jsonify({"error": str(e)})




def main():
    global green_agent
    
    domains_path = os.path.join(os.path.dirname(__file__), "..", "domains")
    
    logger.info(f"Initializing green agent with domains path: {domains_path}")
    green_agent = GreenAgent(domains_path)
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('AGENT_PORT', '8001'))
    
    logger.info(f"Starting green agent server on {host}:{port}")
    app.run(host=host, port=port, debug=False)




if __name__ == "__main__":
    main()
