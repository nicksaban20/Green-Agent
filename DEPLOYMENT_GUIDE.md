# Deployment Guide for Tau-Bench Green Agent

## Prerequisites

- Python 3.8+ installed
- `pip` package manager
- (Optional) Google Cloud SDK (`gcloud`) for Cloud Run deployment
- (Optional) Docker for containerized deployment

## Local Testing (Completed ✅)

All local tests have passed:
- ✅ Dependencies installed
- ✅ Single scenario evaluation working
- ✅ Batch evaluation working
- ✅ Integration tests passing
- ✅ AgentBeats controller tested

## Deployment Options

### Option 1: Google Cloud Run (Recommended)

#### Step 1: Install Google Cloud SDK

```bash
# macOS
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

#### Step 2: Authenticate and Set Project

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

#### Step 3: Deploy to Cloud Run

```bash
# Deploy the service
gcloud run deploy tau-bench-green \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300 \
  --port 8010 \
  --set-env-vars HOST=0.0.0.0,AGENT_PORT=8001

# Get the deployment URL
gcloud run services describe tau-bench-green \
  --region us-central1 \
  --format='value(status.url)'
```

#### Step 4: Verify Deployment

```bash
# Test the deployed agent
DEPLOYED_URL=$(gcloud run services describe tau-bench-green --region us-central1 --format='value(status.url)')
curl $DEPLOYED_URL/.well-known/agent-card.json

# Run integration tests
python test_agent.py $DEPLOYED_URL http://localhost:8002
```

### Option 2: Manual VM Deployment

#### Step 1: Provision VM

- Create a VM with public IP (e.g., Google Compute Engine, AWS EC2, DigitalOcean)
- Ensure ports 8001 (agent) and 8010 (controller) are open
- SSH into the VM

#### Step 2: Install Dependencies

```bash
# On the VM
sudo apt update  # For Ubuntu/Debian
sudo apt install -y python3 python3-pip nginx certbot python3-certbot-nginx

# Clone your repository
git clone <your-repo-url>
cd tau_bench_demo

# Install Python dependencies
pip3 install -r requirements.txt
```

#### Step 3: Configure Nginx

Create `/etc/nginx/sites-available/tau-bench`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/tau-bench /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Step 4: Set Up SSL with Let's Encrypt

```bash
sudo certbot --nginx -d your-domain.com
```

#### Step 5: Run with Systemd

Create `/etc/systemd/system/tau-bench.service`:

```ini
[Unit]
Description=Tau-Bench Green Agent
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/tau_bench_demo
Environment="HOST=0.0.0.0"
Environment="AGENT_PORT=8001"
ExecStart=/usr/local/bin/agentbeats run_ctrl
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable tau-bench
sudo systemctl start tau-bench
sudo systemctl status tau-bench
```

### Option 3: Docker Deployment

#### Step 1: Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001 8010

ENV HOST=0.0.0.0
ENV AGENT_PORT=8001

CMD ["agentbeats", "run_ctrl"]
```

#### Step 2: Build and Run

```bash
docker build -t tau-bench-green .
docker run -d -p 8001:8001 -p 8010:8010 --name tau-bench tau-bench-green
```

## AgentBeats Platform Registration

### Step 1: Get Your Deployment URL

After deployment, you'll have a URL like:
- Cloud Run: `https://tau-bench-green-xxxxx.run.app`
- Custom domain: `https://your-domain.com`

### Step 2: Register on AgentBeats

1. Go to https://agentbeats.ai (or your AgentBeats instance)
2. Click "Create Agent" or "Register Agent"
3. Fill in the form:
   - **Name**: "Tau-Bench Green Agent - [Your Name]"
   - **Deployment Type**: Remote
   - **Controller URL**: Your deployed HTTPS URL (e.g., `https://tau-bench-green-xxxxx.run.app`)
   - **Is Green Agent**: ✅ Check this box
   - **Description**: "Evaluates agents on Tau-Bench benchmark for tool-use capabilities in airline and retail domains"
   - **Capabilities**: evaluation, environment_management, tool_orchestration, batch_evaluation, multi_domain_testing
   - **Supported Domains**: airline, retail
4. Click "Create" or "Submit"

### Step 3: Verify Registration

1. Your agent should appear in the AgentBeats dashboard
2. Test by triggering an evaluation from the platform
3. Check that metrics are reported correctly

## Post-Deployment Testing

### Test Agent Card

```bash
curl https://your-deployment-url/.well-known/agent-card.json
```

### Test Single Evaluation

```bash
python test_agent.py https://your-deployment-url http://localhost:8002
```

### Test from AgentBeats Platform

1. Go to your agent in the AgentBeats dashboard
2. Click "Run Evaluation" or "Test"
3. Provide a white agent URL
4. Verify results appear correctly

## Troubleshooting

### Agent Won't Start

- Check logs: `journalctl -u tau-bench -f` (systemd) or container logs
- Verify port 8001 is not in use: `lsof -i :8001`
- Check environment variables are set correctly

### Controller Can't Connect

- Ensure `run.sh` is executable: `chmod +x run.sh`
- Verify `HOST` and `AGENT_PORT` environment variables
- Check firewall rules allow traffic on ports 8001 and 8010

### HTTPS Issues

- Verify SSL certificate is valid: `certbot certificates`
- Check nginx configuration: `sudo nginx -t`
- Ensure DNS points to your server

### Evaluation Timeouts

- Increase timeout in `agent.py` (default: 30s)
- Check white agent is responding
- Verify network connectivity

## Monitoring

### Check Agent Status

```bash
# Local
curl http://localhost:8001/.well-known/agent-card.json

# Remote
curl https://your-deployment-url/.well-known/agent-card.json
```

### View Logs

```bash
# Systemd
sudo journalctl -u tau-bench -f

# Docker
docker logs -f tau-bench

# Cloud Run
gcloud run services logs read tau-bench-green --region us-central1
```

## Next Steps

1. ✅ Deploy to your chosen platform
2. ✅ Register on AgentBeats
3. ✅ Test from the platform
4. ✅ Share your agent URL with others for evaluation
5. ✅ Monitor performance and metrics

## Support

For issues or questions:
- Check the `DEPLOYMENT_CHECKLIST.md`
- Review logs for error messages
- Contact: agentbeats@berkeley.edu


