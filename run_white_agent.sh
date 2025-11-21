#!/bin/bash

# Launch script for Claude White Agent

export HOST=${HOST:-"0.0.0.0"}
export AGENT_PORT=${AGENT_PORT:-8002}

cd "$(dirname "$0")"
python3 white_agent/llm_agent.py
