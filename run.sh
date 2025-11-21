#!/bin/bash

# Launch script for AgentBeats controller

export HOST=${HOST:-"0.0.0.0"}
export AGENT_PORT=${AGENT_PORT:-8001}

cd "$(dirname "$0")"
python -m green_agent.agent

