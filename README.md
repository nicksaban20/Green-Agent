# Tau-Bench Green Agent for AgentBeats

An agentified version of the Tau-Bench benchmark for evaluating agent tool-use capabilities.

## Overview

This project implements a green agent (evaluation agent) that tests white agents on the Tau-Bench benchmark across airline and retail domains.

## Features

- ✅ A2A-compatible green agent for evaluation
- ✅ Support for both airline and retail domains
- ✅ Batch evaluation across multiple scenarios
- ✅ AgentBeats platform integration
- ✅ Local testing with mock white agent
- ✅ Comprehensive metrics tracking

## Project Structure

```
project/
├── run.sh                  # AgentBeats launch script
├── requirements.txt        # Python dependencies
├── Procfile               # Container entry point
├── launcher.py            # Local testing orchestrator
├── green_agent/
│   ├── agent.py          # Main green agent
│   └── environment.py    # Test environment
├── white_agent/
│   └── mock_agent.py     # Mock agent for testing
├── domains/
│   ├── airline/          # Airline domain files
│   └── retail/           # Retail domain files
└── test_cases/
    ├── airline_scenarios.json
    └── retail_scenarios.json
```

## Installation

```bash
pip install -r requirements.txt
```

## Local Testing

### Run with launcher (recommended)

```bash
# Single scenario
python launcher.py --domain airline --scenario airline_success_1

# All scenarios
python launcher.py --all
```

### Run with AgentBeats controller

```bash
agentbeats run_ctrl
# Visit http://localhost:8080 for management UI
```

## Deployment

### Option 1: Cloud Run (Recommended)

```bash
gcloud run deploy tau-bench-green \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Option 2: Manual VM Deployment

1. Provision a VM with public IP
2. Install dependencies
3. Run: `./run.sh`
4. Configure HTTPS with nginx/certbot

## AgentBeats Integration

### Register Your Agent

1. Deploy your agent with HTTPS
2. Go to AgentBeats dashboard
3. Click "Create Agent"
4. Fill in:
   - Name: "Tau-Bench Green Agent"
   - Controller URL: Your deployed URL
   - Check "Is Green Agent"
5. Submit

### Run Assessments

Once registered, others can evaluate their agents against yours through the AgentBeats platform.

## Metrics

The green agent reports:

- **Success Rate**: Percentage of successfully completed tasks
- **Average Time**: Mean completion time per task
- **Turns**: Number of interaction turns per task

## Domains

### Airline

- Flight search and booking
- Cancellation policy handling
- Multi-step booking workflows

### Retail

- Product search
- Order placement
- Return policy handling
- Loyalty program integration

## Development

### Adding New Scenarios

1. Add scenario to `test_cases/{domain}_scenarios.json`
2. Update test data in `domains/{domain}/data.csv`
3. Test locally with launcher

### Modifying Tools

Edit `domains/{domain}/tools.py` to add or modify available tools.

## Troubleshooting

**Issue**: Agent won't start
- Check port 8001 is available
- Verify all dependencies installed
- Check logs for errors

**Issue**: Evaluation times out
- Increase timeout in agent.py (default: 30s)
- Check white agent is responding

**Issue**: Controller can't find agent
- Ensure `run.sh` is executable
- Check HOST and AGENT_PORT environment variables

## License

MIT

## Contact

For questions: [your-email]@berkeley.edu


