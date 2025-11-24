import json
import time
import requests
import uuid
import logging
import re
from flask import Flask, request, jsonify
from typing import Dict, Any, List, Optional
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from green_agent.environment import Environment

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GreenAgent:
    
    def __init__(self, domains_path: str):
        self.domains_path = domains_path
        self.current_env = None
        self.white_agent_url = None
        self.scenario = None
        self.max_turns = 10
        self.context_id = None
        
    def get_agent_card(self) -> Dict[str, Any]:
        return {
            "name": "τ-bench Green Agent",
            "description": "Evaluates agents using τ-bench benchmark for tool-use capabilities in airline and retail domains",
            "version": "1.0.0",
            "capabilities": [
                "evaluation", 
                "environment_management", 
                "tool_orchestration",
                "batch_evaluation",
                "multi_domain_testing"
            ],
            "supported_domains": ["airline", "retail"],
            "metrics": [
                "success_rate",
                "average_completion_time",
                "turns_per_task"
            ],
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
        success = self.current_env.evaluate_success(goal_state)
        
        logger.info(f"Evaluation complete: success={success}, turns={result.get('turns', 0)}, time={end_time - start_time:.2f}s")
        
        if self.current_env:
            self.current_env.close()
        
        return {
            "success": success,
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
            return json.loads(json_str)
        
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
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




@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        message = data.get('message', '')
        context_id = data.get('context_id')
        
        logger.info(f"Received message: {message[:200]}...")
        
        if "Run all scenarios" in message or "--all" in message:
            white_agent_url = None
            for line in message.split('\n'):
                if "White agent URL:" in line:
                    white_agent_url = line.split("White agent URL:")[1].strip()
                    break
            
            if not white_agent_url:
                return jsonify({"error": "Missing white agent URL for batch evaluation"})
            
            result = green_agent.run_all_scenarios(white_agent_url)
            return jsonify(result)
        
        if "Run tau-bench evaluation" in message or "Run τ-bench evaluation" in message:
            lines = message.split('\n')
            domain = None
            scenario = None
            white_agent_url = None
            
            for line in lines:
                if "domain:" in line and "scenario:" in line:
                    parts = line.split("scenario:")
                    domain_part = parts[0].split("domain:")[1].strip().rstrip(',')
                    scenario = parts[1].strip().rstrip('.')
                    domain = domain_part
                elif "domain:" in line:
                    domain = line.split("domain:")[1].strip().rstrip('.')
                elif "scenario:" in line:
                    scenario = line.split("scenario:")[1].strip().rstrip('.')
                elif "White agent URL:" in line:
                    white_agent_url = line.split("White agent URL:")[1].strip()
            
            if not all([domain, scenario, white_agent_url]):
                error_msg = f"Missing required parameters. Domain: {domain}, Scenario: {scenario}, URL: {white_agent_url}"
                logger.error(error_msg)
                return jsonify({"error": error_msg})
            
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
