# τ-bench Green Agent

An evaluation agent for the [τ-bench](https://github.com/sierra-research/tau-bench) benchmark, designed to test AI agents' tool-use capabilities across airline and retail domains.

## Features

- **Dual-domain evaluation**: Tests agents in airline and retail scenarios
- **AgentBeats compatible**: Integrates with the AgentBeats V2 platform
- **Comprehensive metrics**: Tracks success rate, completion time, and interaction turns
- **Mock & LLM agents**: Includes both mock agent (for testing) and Claude LLM agent implementations

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Local Testing

```bash
# Test with mock white agent (recommended for testing)
python launcher.py --domain airline --scenario airline_success_1

# Test with Claude LLM agent
python launcher.py --domain airline --scenario airline_success_1 --llm

# Run all scenarios
python launcher.py --all
```

### Running with AgentBeats Controller

```bash
agentbeats run_ctrl
# Visit http://localhost:8010 for management UI
```

## Project Structure

```
tau_bench_demo/
├── run.sh                     # AgentBeats launch script
├── Procfile                   # Container entry point
├── requirements.txt           # Dependencies
├── launcher.py                # Local testing orchestrator
├── green_agent/
│   ├── agent.py              # Main evaluation agent
│   └── environment.py        # Test environment manager
├── white_agent/
│   ├── mock_agent.py         # Mock agent for testing
│   └── llm_agent.py          # Claude LLM agent
├── domains/
│   ├── airline/              # Airline domain tools & data
│   └── retail/               # Retail domain tools & data
└── test_cases/               # Evaluation scenarios
    ├── airline_scenarios.json
    └── retail_scenarios.json
```

## Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed deployment instructions using:
- Google Cloud Run (recommended)
- Manual VM deployment
- Docker containers

## AgentBeats Registration

1. Deploy your agent with HTTPS
2. Go to [AgentBeats V2](https://v2.agentbeats.org)
3. Register your agent with the controller URL
4. Your agent is now available for evaluation!

## Domains & Scenarios

### Airline Domain
- Flight search and booking
- Cancellation policies
- Multi-step booking workflows

### Retail Domain
- Product search and filtering
- Order placement
- Return policy handling
- Loyalty program integration

## Development

### Adding New Scenarios

1. Add to `test_cases/{domain}_scenarios.json`
2. Update test data in `domains/{domain}/data.csv`
3. Test with `python launcher.py --domain {domain} --scenario {scenario_id}`

### Modifying Tools

Edit `domains/{domain}/tools.py` to add or modify available tools.

## Testing

```bash
# Local integration test
python test_agent.py http://localhost:8001 http://localhost:8002

# Test deployed agent
python test_agent.py https://your-url.com http://localhost:8002
```

## License

MIT

## Contact

agentbeats@berkeley.edu
