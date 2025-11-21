# Deployment Checklist

Before deploying to AgentBeats, ensure all items are checked:

## Code Quality

- [ ] All files have proper imports
- [ ] Logging is configured throughout
- [ ] Error handling in all API endpoints
- [ ] Type hints added where appropriate
- [ ] No hardcoded URLs or credentials

## Functionality

- [ ] Agent card endpoint works: `/.well-known/agent-card.json`
- [ ] Single evaluation works locally
- [ ] Batch evaluation works locally
- [ ] All scenarios can be executed
- [ ] Metrics are properly calculated and returned
- [ ] Environment resets correctly between runs

## AgentBeats Integration

- [ ] `run.sh` exists and is executable
- [ ] `requirements.txt` includes `earthshaker`
- [ ] Agent uses `HOST` and `AGENT_PORT` environment variables
- [ ] Controller can start/stop the agent
- [ ] Context IDs are properly handled

## Deployment

- [ ] Choose deployment method (Cloud Run / VM)
- [ ] HTTPS configured
- [ ] Controller URL is publicly accessible
- [ ] Test with `test_agent.py` script
- [ ] Agent registered on AgentBeats platform

## Testing Commands

```bash
# Local testing
python launcher.py --all

# Controller testing
agentbeats run_ctrl

# Integration testing
python test_agent.py http://localhost:8001 http://localhost:8002

# Remote testing
python test_agent.py https://your-deployment-url.run.app http://localhost:8002
```

## Post-Deployment

- [ ] Agent appears in AgentBeats dashboard
- [ ] Can trigger evaluation from platform
- [ ] Metrics are reported correctly
- [ ] Leaderboard updates properly


