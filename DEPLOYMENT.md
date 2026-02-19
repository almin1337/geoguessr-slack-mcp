# Server Deployment Guide

This guide covers deploying the GeoGuessr Slack integration to run on a server instead of your local laptop.

## Option 1: GitHub Actions (Recommended - Free)

GitHub Actions can run your script on a schedule without needing a server.

### Setup

1. **Create a GitHub repository** (or use existing) and push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/geoguessr-slack-mcp.git
   git push -u origin main
   ```

2. **Add secrets** in GitHub repository settings:
   - Go to Settings → Secrets and variables → Actions
   - Add these secrets:
     - `GEOGUESSR_COOKIE`: Your `_ncfa` cookie value
     - `SLACK_BOT_TOKEN`: Your Slack bot token
     - `SLACK_CHANNEL_ID`: Your Slack channel ID

3. **Create `.github/workflows/daily-challenge.yml`**:
   ```yaml
   name: Daily GeoGuessr Challenge

   on:
     schedule:
       # Run hourly from 8:00 to 15:00 UTC (adjust timezone as needed)
       # For 8:00-15:00 local time, adjust these cron times
       # Example: If you're UTC+1, 8:00 local = 7:00 UTC, 15:00 local = 14:00 UTC
       - cron: '0 7-14 * * 1-5'  # Every hour from 7-14 UTC, Mon-Fri
     workflow_dispatch:  # Allow manual trigger

   jobs:
     run-challenge:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         
         - name: Set up Python
           uses: actions/setup-python@v5
           with:
             python-version: '3.11'
         
         - name: Install dependencies
           run: |
             pip install -r requirements.txt
             pip install playwright
             playwright install chromium
         
         - name: Run daily challenge
           env:
             GEOGUESSR_COOKIE: ${{ secrets.GEOGUESSR_COOKIE }}
             SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
             SLACK_CHANNEL_ID: ${{ secrets.SLACK_CHANNEL_ID }}
           run: |
             python daily_softhouse_challenge.py
   ```

4. **Adjust timezone**: GitHub Actions runs in UTC. If you want 8:00-15:00 in your local timezone:
   - Find your UTC offset (e.g., UTC+1 means subtract 1 hour)
   - Update the cron schedule accordingly
   - Example: For UTC+1, 8:00 local = 7:00 UTC, so use `'0 7-14 * * 1-5'`

**Pros:**
- Free for public repos (2000 minutes/month for private)
- No server maintenance
- Automatic runs even if your laptop is off
- Easy to monitor via GitHub Actions UI

**Cons:**
- Requires GitHub account
- State file (`.daily_challenge_state`) needs to be stored elsewhere (GitHub Actions doesn't persist files between runs)

### State Management for GitHub Actions

Since GitHub Actions doesn't persist files, you'll need to store state externally. Options:

**Option A: Use GitHub Gists API**
- Store `.daily_challenge_state` as a Gist
- Read/write via GitHub API

**Option B: Use a simple database**
- Use a free service like Supabase, Firebase, or MongoDB Atlas
- Store state as JSON

**Option C: Use GitHub repository file**
- Commit `.daily_challenge_state` to the repo
- Read/write via GitHub API

## Option 2: Cloud VM (AWS EC2, DigitalOcean, etc.)

Deploy to a cloud virtual machine that runs 24/7.

### Setup (DigitalOcean example)

1. **Create a Droplet** (Ubuntu 22.04, smallest size is fine ~$6/month)

2. **SSH into the server**:
   ```bash
   ssh root@your-server-ip
   ```

3. **Install dependencies**:
   ```bash
   apt update
   apt install -y python3 python3-pip git
   pip3 install virtualenv
   ```

4. **Clone and setup**:
   ```bash
   cd /opt
   git clone https://github.com/yourusername/geoguessr-slack-mcp.git
   cd geoguessr-slack-mcp
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install playwright
   playwright install chromium
   ```

5. **Create `.env` file**:
   ```bash
   nano .env
   # Add your credentials
   ```

6. **Setup cron**:
   ```bash
   crontab -e
   ```
   Add:
   ```
   # Run hourly from 8:00 to 15:00 on weekdays
   0 8-15 * * 1-5 cd /opt/geoguessr-slack-mcp && /opt/geoguessr-slack-mcp/venv/bin/python daily_softhouse_challenge.py >> /var/log/geoguessr.log 2>&1
   ```

**Pros:**
- Full control
- Can persist state files
- Can run other services

**Cons:**
- Costs money (~$6-20/month)
- Requires server maintenance
- Need to secure the server

## Option 3: Railway / Render / Fly.io (Platform as a Service)

Deploy as a scheduled job on a PaaS platform.

### Railway Example

1. **Install Railway CLI**:
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Create `railway.json`**:
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "python daily_softhouse_challenge.py",
       "restartPolicyType": "ON_FAILURE"
     }
   }
   ```

3. **Setup cron job** (Railway supports cron):
   - In Railway dashboard, add a cron job: `0 8-15 * * 1-5`

**Pros:**
- Easy deployment
- Free tier available
- Automatic scaling

**Cons:**
- May require adapting for their platform
- State persistence varies by platform

## Option 4: AWS Lambda / Google Cloud Functions

Serverless functions that run on a schedule.

### AWS Lambda Example

1. **Create Lambda function** with Python runtime

2. **Set up EventBridge (CloudWatch Events)** rule:
   - Schedule: `cron(0 8-15 ? * MON-FRI *)`
   - Target: Your Lambda function

3. **Package dependencies**:
   ```bash
   pip install -r requirements.txt -t .
   zip -r function.zip .
   ```

4. **Upload to Lambda** and configure environment variables

**Pros:**
- Pay per execution (very cheap)
- Highly scalable
- No server management

**Cons:**
- More complex setup
- Playwright/Chromium may need special handling (use AWS Lambda Layers or headless Chrome)
- 15-minute execution limit

## Recommended: GitHub Actions with State Storage

For simplicity and cost-effectiveness, use **GitHub Actions** with one of these state storage options:

1. **GitHub Gist** (simplest)
2. **GitHub repository file** (committed to repo)
3. **External database** (Supabase free tier)

Would you like me to implement one of these options? I can create the GitHub Actions workflow and add state persistence via Gist or GitHub API.
