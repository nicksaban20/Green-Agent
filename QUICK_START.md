# Quick Start Guide

## ✅ What's Ready

All implementation and testing is complete:
- ✅ All files created and configured
- ✅ Dependencies installed
- ✅ Local tests passing
- ✅ AgentBeats controller tested
- ✅ Deployment guide created

## 🚀 Next Steps to Deploy

### If You Have Google Cloud SDK:

```bash
# 1. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Deploy
gcloud run deploy tau-bench-green \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300

# 3. Get URL
gcloud run services describe tau-bench-green \
  --region us-central1 \
  --format='value(status.url)'
```

### If You Don't Have Google Cloud SDK:

1. **Install Google Cloud SDK** (if you want Cloud Run):
   ```bash
   # macOS
   brew install google-cloud-sdk
   ```

2. **Or use a VM/Server**:
   - Follow instructions in `DEPLOYMENT_GUIDE.md` (Option 2)
   - Set up nginx and SSL
   - Run with systemd

3. **Or use Docker**:
   - Follow instructions in `DEPLOYMENT_GUIDE.md` (Option 3)
   - Deploy to any container platform

## 📋 Registration Checklist

After deployment:

- [ ] Agent is accessible via HTTPS
- [ ] Agent card endpoint works: `/.well-known/agent-card.json`
- [ ] Test with: `python test_agent.py <your-url> <white-agent-url>`
- [ ] Register on AgentBeats platform
- [ ] Test evaluation from platform

## 📚 Documentation

- `README.md` - Project overview
- `DEPLOYMENT_GUIDE.md` - Detailed deployment instructions
- `DEPLOYMENT_CHECKLIST.md` - Pre-deployment checklist
- `test_agent.py` - Integration test script

## 🧪 Test Commands

```bash
# Local testing
python launcher.py --domain airline --scenario airline_success_1
python launcher.py --all

# Integration testing (with agents running)
python test_agent.py http://localhost:8001 http://localhost:8002

# Controller testing
agentbeats run_ctrl
# Visit http://localhost:8010 for management UI
```

## 📞 Support

See `DEPLOYMENT_GUIDE.md` for troubleshooting and detailed instructions.


