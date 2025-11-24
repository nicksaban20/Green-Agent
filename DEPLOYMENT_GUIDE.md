# Deployment Guide

## Prerequisites

- Python 3.8+
- AgentBeats (`earthshaker`) installed
- (Optional) Google Cloud SDK for Cloud Run deployment

## Deployment Methods

### Option 1: Cloud Run (Recommended)

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy
gcloud run deploy tau-bench-green \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300

# Get URL
gcloud run services describe tau-bench-green \
  --region us-central1 \
  --format='value(status.url)'
```

### Option 2: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8010

CMD ["agentbeats", "run_ctrl"]
```

Build and run:
```bash
docker build -t tau-bench-green .
docker run -d -p 8010:8010 tau-bench-green
```

### Option 3: Manual VM

1. Provision VM with public IP
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure systemd service:
   ```ini
   [Unit]
   Description=Tau-Bench Green Agent
   After=network.target

   [Service]
   Type=simple
   WorkingDirectory=/path/to/tau_bench_demo
   ExecStart=/usr/local/bin/agentbeats run_ctrl
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
4. Enable and start:
   ```bash
   sudo systemctl enable tau-bench
   sudo systemctl start tau-bench
   ```

## Register on AgentBeats

1. Navigate to https://v2.agentbeats.org
2. Click "Add Agent"
3. Enter your controller URL (must be HTTPS)
4. Click "Check" to verify
5. Click "Add" to register

## Verification

```bash
# Test agent card
curl https://your-url/.well-known/agent-card.json

# Test evaluation
python test_agent.py https://your-url http://localhost:8002
```

## Troubleshooting

**Agent won't start**
- Check port 8010 is available: `lsof -i :8010`
- Verify `run.sh` is executable: `chmod +x run.sh`

**Controller can't find agent**
- Ensure `HOST` and `AGENT_PORT` environment variables are set
- Check logs for errors

**HTTPS required**
- Cloud Run provides HTTPS automatically
- For VMs, use nginx + Let's Encrypt:
  ```bash
  sudo certbot --nginx -d your-domain.com
  ```

## Monitoring

```bash
# View logs (systemd)
sudo journalctl -u tau-bench -f

# View logs (Docker)
docker logs -f tau-bench-green

# View logs (Cloud Run)
gcloud run services logs read tau-bench-green --region us-central1
```
