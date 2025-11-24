import argparse
import json
import time
import requests
import subprocess
import sys
import os
from typing import Dict, Any, List


class TauBenchLauncher:
    
    def __init__(self, use_llm=False):
        self.use_llm = use_llm
        self.green_agent_process = None
        self.white_agent_process = None
        self.green_agent_url = "http://localhost:8001"
        self.white_agent_url = "http://localhost:8002"
        
    def start_agents(self):
        print("Starting green agent on port 8001...")
        self.green_agent_process = subprocess.Popen([
            sys.executable, 
            os.path.join(os.path.dirname(__file__), "green_agent", "agent.py")
        ])
        
        if self.use_llm:
            print("🤖 Launching CLAUDE Agent on port 8002...")
            agent_script = "llm_agent.py"
        else:
            print("🎭 Launching MOCK Agent on port 8002...")
            agent_script = "mock_agent.py"

        self.white_agent_process = subprocess.Popen([
            sys.executable,
            os.path.join(os.path.dirname(__file__), "white_agent", agent_script)
        ])
        
        print("Waiting for agents to be ready...")
        self._wait_for_agents()
        print("Both agents ready.")
        
    def _wait_for_agents(self, timeout=30):
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.green_agent_url}/agent-card", timeout=5)
                if response.status_code == 200:
                    response = requests.get(f"{self.white_agent_url}/agent-card", timeout=5)
                    if response.status_code == 200:
                        return True
            except requests.RequestException:
                pass
            
            time.sleep(1)
        
        raise Exception("Agents failed to start within timeout")
    
    def run_evaluation(self, domain: str, scenario: str) -> Dict[str, Any]:
        print(f"Running evaluation: domain={domain}, scenario={scenario}")
        
        task_message = f"""Run tau-bench evaluation on domain: {domain}, scenario: {scenario}.
White agent URL: {self.white_agent_url}"""
        
        try:
            response = requests.post(
                f"{self.green_agent_url}/send-message",
                json={"message": task_message},
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            print("Evaluation complete.")
            return result
            
        except requests.RequestException as e:
            return {"error": f"Failed to run evaluation: {e}"}
    
    def run_all_scenarios(self):
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
        
        for domain, scenario in scenarios:
            print(f"\n{'='*50}")
            print(f"Running: {domain} - {scenario}")
            print(f"{'='*50}")
            
            result = self.run_evaluation(domain, scenario)
            results.append({
                "domain": domain,
                "scenario": scenario,
                "result": result
            })
            
            self._display_result(result)
            
            time.sleep(1)
        
        return results
    
    def _display_result(self, result: Dict[str, Any]):
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            success = result.get('success', False)
            turns = result.get('turns', 0)
            time_used = result.get('time_used', 0)
            
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} Success: {success}")
            print(f"📊 Turns: {turns}")
            print(f"⏱️  Time: {time_used:.2f}s")
            
            if result.get('conversation_history'):
                print(f"💬 Conversation: {len(result['conversation_history'])} interactions")
    
    def test_controller_integration(self):
        """Test if the agent can be reset via controller"""
        print("Testing controller integration...")
        
        try:
            try:
                response = requests.get(f"{self.green_agent_url}/status", timeout=5)
            except requests.RequestException:
                pass
            
            response = requests.get(f"{self.green_agent_url}/.well-known/agent-card.json", timeout=5)
            if response.status_code == 200:
                print("✅ Agent card accessible")
                agent_card = response.json()
                print(f"   Agent: {agent_card.get('name')}")
                print(f"   Version: {agent_card.get('version')}")
            
            try:
                response = requests.post(f"{self.green_agent_url}/reset", timeout=5)
                if response.status_code == 200:
                    print("✅ Agent reset successful")
            except requests.RequestException:
                print("⚠️  Reset endpoint not available (controller may not be running)")
            
            return True
            
        except requests.RequestException as e:
            print(f"❌ Controller integration test failed: {e}")
            return False
    
    def stop_agents(self):
        print("\nStopping agents...")
        
        if self.green_agent_process:
            self.green_agent_process.terminate()
            self.green_agent_process.wait()
        
        if self.white_agent_process:
            self.white_agent_process.terminate()
            self.white_agent_process.wait()
        
        print("Agents stopped.")
    
    def cleanup(self):
        self.stop_agents()


def main():
    parser = argparse.ArgumentParser(description="τ-bench Demo Launcher")
    parser.add_argument("--domain", choices=["airline", "retail"], help="Domain to evaluate")
    parser.add_argument("--scenario", help="Scenario ID to run")
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    parser.add_argument("--llm", action="store_true", help="Use Claude LLM agent")
    
    args = parser.parse_args()
    
    launcher = TauBenchLauncher(use_llm=args.llm)
    
    try:
        launcher.start_agents()
        launcher.test_controller_integration()
        
        if args.all:
            results = launcher.run_all_scenarios()
            
            print(f"\n{'='*50}")
            print("SUMMARY")
            print(f"{'='*50}")
            
            success_count = 0
            total_count = len(results)
            
            for result in results:
                if result["result"].get("success", False):
                    success_count += 1
            
            print(f"Total scenarios: {total_count}")
            print(f"Successful: {success_count}")
            print(f"Failed: {total_count - success_count}")
            print(f"Success rate: {success_count/total_count*100:.1f}%")
            
        elif args.domain and args.scenario:
            result = launcher.run_evaluation(args.domain, args.scenario)
            launcher._display_result(result)
            
        else:
            print("Please specify --domain and --scenario, or use --all to run all scenarios")
            return 1
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        launcher.cleanup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

