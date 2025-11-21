#!/usr/bin/env python3
"""Test script for validating the green agent implementation."""

import requests
import json
import time
import sys

def test_agent_card(base_url):
    """Test that agent card is accessible."""
    print("Testing agent card...")
    try:
        response = requests.get(f"{base_url}/.well-known/agent-card.json", timeout=5)
        response.raise_for_status()
        card = response.json()
        print(f"✅ Agent card OK: {card.get('name')}")
        return True
    except Exception as e:
        print(f"❌ Agent card failed: {e}")
        return False

def test_single_evaluation(green_url, white_url):
    """Test a single evaluation."""
    print("\nTesting single evaluation...")
    message = f"""Run tau-bench evaluation on domain: airline, scenario: airline_success_1.
White agent URL: {white_url}"""
    try:
        response = requests.post(f"{green_url}/send-message", json={"message": message}, timeout=60)
        response.raise_for_status()
        result = response.json()
        if result.get('success'):
            print(f"✅ Evaluation succeeded in {result.get('turns')} turns")
            return True
        else:
            print(f"⚠️  Evaluation completed but task failed")
            return False
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return False

def test_batch_evaluation(green_url, white_url):
    """Test batch evaluation."""
    print("\nTesting batch evaluation...")
    message = f"""Run all scenarios.
White agent URL: {white_url}"""
    try:
        response = requests.post(f"{green_url}/send-message", json={"message": message}, timeout=300)
        response.raise_for_status()
        result = response.json()
        metrics = result.get('aggregate_metrics', {})
        success_rate = metrics.get('success_rate', 0)
        print(f"✅ Batch evaluation completed: {success_rate:.1%} success rate")
        return True
    except Exception as e:
        print(f"❌ Batch evaluation failed: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python test_agent.py <green_agent_url> <white_agent_url>")
        print("Example: python test_agent.py http://localhost:8001 http://localhost:8002")
        sys.exit(1)
    green_url = sys.argv[1].rstrip('/')
    white_url = sys.argv[2].rstrip('/')
    print(f"Testing green agent at: {green_url}")
    print(f"Using white agent at: {white_url}")
    print("=" * 60)
    results = []
    results.append(("Agent Card", test_agent_card(green_url)))
    time.sleep(1)
    results.append(("Single Evaluation", test_single_evaluation(green_url, white_url)))
    time.sleep(1)
    results.append(("Batch Evaluation", test_batch_evaluation(green_url, white_url)))
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("\n🎉 All tests passed! Ready for deployment.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please fix before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()


