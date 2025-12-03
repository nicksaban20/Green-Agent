# Deployment Guide

## Prerequisites

- Python 3.8+
- AgentBeats (`earthshaker`) installed
- `cloudflared` installed (for tunneling)

## 🚀 Step-by-Step Deployment (Verified)

Follow these steps exactly to deploy your agent.

### 1. Start Tunnel & Get Hostname

First, start the tunnel to get your public hostname.

```bash
# Start cloudflared on port 8010
cloudflared tunnel --url http://localhost:8010
```

**Copy the URL** that appears (e.g., `https://your-hostname.trycloudflare.com`).
*Keep this terminal running.*

### 2. Start Controller

Open a **new terminal** and start the controller, setting the `CLOUDRUN_HOST` variable to your hostname (without `https://`).

```bash
# Replace with YOUR hostname from Step 1
export CLOUDRUN_HOST=your-hostname.trycloudflare.com

# Start the controller
agentbeats run_ctrl
```

*Keep this terminal running.*

### 3. Verify & Fix Agent State

Open a **third terminal** to verify the agent is running and accessible.

1. **Find your Agent ID**:
   ```bash
   curl -s http://localhost:8010/agents
   ```
   *Copy the long ID string (e.g., `ca3f0cc69394404ba8155e19127cd1d1`).*

2. **Apply Manual Fix** (Required for local discovery):
   ```bash
   # Replace AGENT_ID with your actual ID
   AGENT_ID=your_agent_id_here
   
   # Create agent card file
   curl -s http://localhost:$(curl -s http://localhost:8010/agents | grep internal_port | awk -F': ' '{print $2}' | tr -d ',')/.well-known/agent-card.json > .ab/agents/$AGENT_ID/agent_card
   
   # Force state to running
   echo "running" > .ab/agents/$AGENT_ID/state
   ```

### 4. Register on AgentBeats

1. Go to [AgentBeats V2](https://v2.agentbeats.org)
2. Click "Add Agent"
3. Enter your **Controller URL**: `https://your-hostname.trycloudflare.com`
4. Click "Check" -> "Add"

## Troubleshooting

**"Agent Card URL contains a local IP address"**
- This means `CLOUDRUN_HOST` wasn't set correctly.
- Stop the controller (Ctrl+C).
- Restart it with: `CLOUDRUN_HOST=your-hostname.trycloudflare.com agentbeats run_ctrl`

**Agent stuck in "starting" state**
- This is a known issue with local discovery.
- Run the "Apply Manual Fix" commands in Step 3.

**Controller URL not reachable**
- Ensure `cloudflared` is still running.
- Check that you copied the correct URL from Step 1.
